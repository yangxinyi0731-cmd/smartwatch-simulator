from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from research.early_risk.common import PROJECT_ROOT
from research.early_risk.upload_analysis import NORMALIZED_RATE_HZ, analyze_normalized_imu


CASE_NAME = re.compile(
    r"^P(?P<participant>\d{2})-(?P<action>大幅度摆臂|安全失衡|弯腰捡东西|快速坐下|正常坐下|走路)-(?P<repetition>\d{2})\.zip$"
)
ACTION_CODES = {
    "大幅度摆臂": "large_arm_swing",
    "安全失衡": "controlled_instability",
    "弯腰捡东西": "bend_and_pick",
    "快速坐下": "rapid_sit",
    "正常坐下": "normal_sit",
    "走路": "walking",
}
EXPECTED_INNER_FILES = {
    "Accelerometer.csv",
    "Gyroscope.csv",
    "meta/device.csv",
    "meta/time.csv",
}
MAX_OUTER_ENTRIES = 100
MAX_INNER_ARCHIVE_BYTES = 10 * 1024 * 1024
MAX_INNER_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS_PER_SENSOR = 100_000


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_zip_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"压缩包包含不安全路径：{name}")
    return normalized


def _read_entry(archive: zipfile.ZipFile, name: str) -> bytes:
    info = archive.getinfo(name)
    if info.is_dir() or info.file_size > MAX_INNER_FILE_BYTES:
        raise ValueError(f"内层文件大小或类型无效：{name}")
    payload = archive.read(info)
    if len(payload) != info.file_size:
        raise ValueError(f"内层文件读取不完整：{name}")
    return payload


def _parse_sensor_csv(payload: bytes, expected_unit: str) -> tuple[np.ndarray, np.ndarray]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("传感器 CSV 必须使用 UTF-8 编码。") from exc
    reader = csv.reader(io.StringIO(text))
    try:
        header = tuple(cell.strip().strip('"') for cell in next(reader))
    except StopIteration as exc:
        raise ValueError("传感器 CSV 为空。") from exc
    expected_header = ("Time (s)", f"X ({expected_unit})", f"Y ({expected_unit})", f"Z ({expected_unit})")
    if header != expected_header:
        raise ValueError(f"传感器 CSV 表头不符合预期：{header}")

    times: list[float] = []
    values: list[list[float]] = []
    for row_number, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(times) >= MAX_ROWS_PER_SENSOR:
            raise ValueError("单个传感器文件采样点过多。")
        if len(row) != 4:
            raise ValueError(f"传感器 CSV 第 {row_number} 行列数不正确。")
        try:
            parsed = [float(cell) for cell in row]
        except ValueError as exc:
            raise ValueError(f"传感器 CSV 第 {row_number} 行包含非数字。") from exc
        if not all(math.isfinite(value) for value in parsed):
            raise ValueError(f"传感器 CSV 第 {row_number} 行包含无效数值。")
        times.append(parsed[0])
        values.append(parsed[1:])

    if len(times) < 50:
        raise ValueError("传感器记录不足 50 个采样点。")
    time_array = np.asarray(times, dtype=np.float64)
    value_array = np.asarray(values, dtype=np.float64)
    order = np.argsort(time_array, kind="stable")
    time_array = time_array[order]
    value_array = value_array[order]
    unique_times, unique_indices = np.unique(time_array, return_index=True)
    return unique_times, value_array[unique_indices]


def _stream_quality(times: np.ndarray) -> dict[str, float | int]:
    deltas = np.diff(times)
    if len(deltas) == 0 or np.any(deltas <= 0):
        raise ValueError("传感器时间列无法整理为严格递增序列。")
    median_delta = float(np.median(deltas))
    rate_hz = 1.0 / median_delta
    if not 5.0 <= rate_hz <= 400.0:
        raise ValueError(f"推算采样率超出 5–400 Hz：{rate_hz:.3f}")
    return {
        "sample_count": int(len(times)),
        "sample_rate_hz": round(rate_hz, 3),
        "max_gap_ms": round(float(np.max(deltas) * 1000), 3),
    }


def _align_and_resample(
    acceleration_times: np.ndarray,
    acceleration_values: np.ndarray,
    gyroscope_times: np.ndarray,
    gyroscope_values: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    acceleration_quality = _stream_quality(acceleration_times)
    gyroscope_quality = _stream_quality(gyroscope_times)
    common_start = max(float(acceleration_times[0]), float(gyroscope_times[0]))
    common_end = min(float(acceleration_times[-1]), float(gyroscope_times[-1]))
    duration_s = common_end - common_start
    if duration_s < 1.0:
        raise ValueError("加速度和角速度的共同时间范围不足 1 秒。")

    target_times = np.arange(common_start, common_end + 1e-9, 1.0 / NORMALIZED_RATE_HZ)
    acceleration = np.column_stack(
        [np.interp(target_times, acceleration_times, acceleration_values[:, axis]) for axis in range(3)]
    )
    gyroscope = np.column_stack(
        [np.interp(target_times, gyroscope_times, gyroscope_values[:, axis]) for axis in range(3)]
    )
    values = np.column_stack([acceleration, gyroscope]).astype(np.float32)
    if not np.isfinite(values).all():
        raise ValueError("时间对齐后出现无效数值。")
    return values, {
        "acceleration": acceleration_quality,
        "gyroscope": gyroscope_quality,
        "common_start_offset_ms": round(common_start * 1000, 3),
        "source_end_skew_ms": round(abs(float(acceleration_times[-1]) - float(gyroscope_times[-1])) * 1000, 3),
        "normalized_sample_rate_hz": NORMALIZED_RATE_HZ,
        "normalized_sample_count": int(len(values)),
        "duration_s": round((len(values) - 1) / NORMALIZED_RATE_HZ, 3),
    }


def _canonical_csv(values: np.ndarray) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("time_s", "ax", "ay", "az", "gx", "gy", "gz"))
    for index, row in enumerate(values):
        writer.writerow((f"{index / NORMALIZED_RATE_HZ:.2f}", *(f"{float(value):.7g}" for value in row)))
    return output.getvalue().encode("utf-8")


def _compact_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    activity = analysis["activity_model"]
    fall = analysis["fall_model"]
    risk = analysis["early_risk_model"]
    return {
        "activity": {
            "status": activity["status"],
            "label": activity.get("label"),
        },
        "fall_screening": {
            "status": fall["status"],
            "screening": fall.get("screening"),
            "max_score": fall.get("max_score"),
            "threshold": fall.get("threshold"),
            "candidate_window_count": len(fall.get("candidate_windows", [])),
        },
        "early_risk_proxy": {
            "status": risk["status"],
            "max_scores": risk.get("max_scores"),
            "attention_detected": risk.get("attention_detected"),
        },
        "interpretation": {
            "current_activity": analysis["interpretation"]["current_activity"],
            "review_required": analysis["interpretation"]["review_required"],
            "conclusion": analysis["interpretation"]["conclusion"],
        },
    }


def import_archive(source_archive: Path, output_root: Path) -> dict[str, Any]:
    source_archive = source_archive.resolve(strict=True)
    output_root = output_root.resolve()
    if output_root != PROJECT_ROOT.resolve() and PROJECT_ROOT.resolve() not in output_root.parents:
        raise ValueError("输出目录必须位于项目内。")

    archive_sha256 = hashlib.sha256(source_archive.read_bytes()).hexdigest()
    case_dir = output_root / "data" / "cases" / "self_collected_p01"
    catalog_path = output_root / "data" / "catalog" / "self_collected_pending_v1.json"
    report_path = output_root / "reports" / "early_risk" / "self_collected_p01_engineering_validation_v1.json"
    case_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    registry_cases: list[dict[str, Any]] = []
    report_cases: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    action_counts: Counter[str] = Counter()
    fall_candidates: Counter[str] = Counter()
    review_counts: Counter[str] = Counter()

    with zipfile.ZipFile(source_archive) as outer:
        if len(outer.infolist()) > MAX_OUTER_ENTRIES:
            raise ValueError("外层压缩包条目过多。")
        nested_entries = []
        for info in outer.infolist():
            safe_name = _safe_zip_name(info.filename)
            if info.is_dir():
                continue
            if info.file_size > MAX_INNER_ARCHIVE_BYTES:
                raise ValueError(f"内层压缩包过大：{safe_name}")
            if not safe_name.lower().endswith(".zip"):
                raise ValueError(f"外层压缩包包含非预期文件：{safe_name}")
            nested_entries.append(info)

        for info in sorted(nested_entries, key=lambda item: item.filename):
            nested_name = PurePosixPath(info.filename.replace("\\", "/")).name
            match = CASE_NAME.fullmatch(nested_name)
            if match is None:
                errors.append({"entry": nested_name, "error": "文件名不符合 Pxx-动作-序号.zip 规则。"})
                continue
            participant_id = f"P{match.group('participant')}"
            action_label = match.group("action")
            action_code = ACTION_CODES[action_label]
            repetition = int(match.group("repetition"))
            case_id = f"self-{participant_id.lower()}-{action_code.replace('_', '-')}-{repetition:02d}"
            nested_payload = outer.read(info)
            try:
                with zipfile.ZipFile(io.BytesIO(nested_payload)) as inner:
                    names = {_safe_zip_name(item.filename) for item in inner.infolist() if not item.is_dir()}
                    if names != EXPECTED_INNER_FILES:
                        raise ValueError(f"内层文件集合不完整：{sorted(names)}")
                    acceleration_times, acceleration_values = _parse_sensor_csv(
                        _read_entry(inner, "Accelerometer.csv"), "m/s^2"
                    )
                    gyroscope_times, gyroscope_values = _parse_sensor_csv(
                        _read_entry(inner, "Gyroscope.csv"), "rad/s"
                    )
                values, quality = _align_and_resample(
                    acceleration_times,
                    acceleration_values,
                    gyroscope_times,
                    gyroscope_values,
                )
                canonical_payload = _canonical_csv(values)
                canonical_name = f"{case_id}.csv"
                canonical_path = case_dir / canonical_name
                canonical_path.write_bytes(canonical_payload)
                analysis = analyze_normalized_imu(values)
                compact_analysis = _compact_analysis(analysis)
            except Exception as exc:  # noqa: BLE001 - batch import must preserve per-case failure evidence
                errors.append({"entry": nested_name, "error": str(exc)})
                continue

            action_counts[action_label] += 1
            candidate_count = compact_analysis["fall_screening"]["candidate_window_count"]
            if candidate_count:
                fall_candidates[action_label] += 1
            if compact_analysis["interpretation"]["review_required"]:
                review_counts[action_label] += 1
            canonical_relative_path = canonical_path.relative_to(output_root).as_posix()
            case_record = {
                "case_id": case_id,
                "participant_id": participant_id,
                "action_code": action_code,
                "action_label": action_label,
                "repetition": repetition,
                "truth_category": "REAL_LAB_ACTIVITY",
                "label_source": "provided_archive_filename",
                "source_archive_entry": nested_name,
                "source_entry_sha256": _sha256_bytes(nested_payload),
                "canonical_relative_path": canonical_relative_path,
                "canonical_sha256": _sha256_bytes(canonical_payload),
                "duration_s": quality["duration_s"],
                "normalized_sample_count": quality["normalized_sample_count"],
                "accepted_for_engineering_validation": True,
            }
            registry_cases.append(case_record)
            report_cases.append({**case_record, "source_quality": quality, "analysis": compact_analysis})

    registry_cases.sort(key=lambda case: case["case_id"])
    report_cases.sort(key=lambda case: case["case_id"])
    expected_count = 30
    expected_action_counts = {action_label: 5 for action_label in ACTION_CODES}
    accepted_count = len(registry_cases)
    case_ids = [case["case_id"] for case in registry_cases]
    cohort_checks = {
        "expected_total": accepted_count == expected_count,
        "unique_case_ids": len(case_ids) == len(set(case_ids)),
        "participant_is_p01": {case["participant_id"] for case in registry_cases} == {"P01"},
        "six_actions_five_repetitions_each": dict(action_counts) == expected_action_counts,
    }
    claim_enabled = all(cohort_checks.values()) and not errors
    generated_at = datetime.now(timezone.utc).astimezone().isoformat()
    registry = {
        "registry_version": "1.1.0",
        "status": "ENGINEERING_VALIDATED" if claim_enabled else "REVIEW_REQUIRED",
        "expected_case_count": expected_count,
        "received_case_count": len(nested_entries),
        "accepted_case_count": accepted_count,
        "rejected_case_count": len(errors),
        "participant_count": len({case["participant_id"] for case in registry_cases}),
        "action_count": len(action_counts),
        "claim_enabled": claim_enabled,
        "claim_scope": "自主采集六轴数据接入与冻结模型工程验证" if claim_enabled else "尚未完成",
        "cases": registry_cases,
        "required_channels": ["ax", "ay", "az", "gx", "gy", "gz"],
        "canonical_sample_rate_hz": NORMALIZED_RATE_HZ,
        "canonical_units": ["m/s^2", "m/s^2", "m/s^2", "rad/s", "rad/s", "rad/s"],
        "source_archive": {
            "file_name": source_archive.name,
            "sha256": archive_sha256,
            "raw_archive_committed": False,
            "metadata_committed": False,
        },
        "cohort_checks": cohort_checks,
        "generated_at": generated_at,
        "note": "30组记录来自同一匿名参与者P01。仓库只保存去除设备信息和绝对时间后的50Hz六轴文件；该结果仅支持数据接入与冻结模型工程验证，不支持真实跌倒预测、跨人群泛化或医疗结论。",
    }
    report = {
        "report_version": "1.0.0",
        "generated_at": generated_at,
        "source": registry["source_archive"],
        "scope": {
            "participant_count": registry["participant_count"],
            "received_case_count": len(nested_entries),
            "accepted_case_count": accepted_count,
            "rejected_case_count": len(errors),
            "action_counts": dict(sorted(action_counts.items())),
            "label_source": "压缩包文件名；未提供独立视频或第二标注者复核。",
            "consent_documentation_in_archive": False,
            "model_parameters_changed": False,
        },
        "engineering_results": {
            "all_files_quality_accepted": claim_enabled,
            "cohort_checks": cohort_checks,
            "full_three_model_pipeline_case_count": sum(
                1
                for case in report_cases
                if all(
                    case["analysis"][key]["status"] == "COMPLETED"
                    for key in ("activity", "fall_screening", "early_risk_proxy")
                )
            ),
            "fall_candidate_case_count": sum(fall_candidates.values()),
            "fall_candidate_case_count_by_action": dict(sorted(fall_candidates.items())),
            "manual_review_case_count": sum(review_counts.values()),
            "manual_review_case_count_by_action": dict(sorted(review_counts.items())),
        },
        "cases": report_cases,
        "errors": errors,
        "allowed_claim": "团队完成了1名匿名参与者、6类受控动作、30组腕部六轴数据的自主采集，并使用未针对该参与者调参的既有模型完成数据接入和工程验证。",
        "limitations": [
            "30组记录全部来自同一匿名参与者P01，不能证明跨参与者泛化能力。",
            "动作标签来自文件名，压缩包未包含视频、独立标注者复核或知情同意文件。",
            "所有动作均按受控活动处理；安全失衡不是实际跌倒，其他类别也不是跌倒样本。",
            "模型参数未使用P01数据训练或调整；报告只验证数据接入、质量和冻结模型运行。",
            "提前风险输出仍是公开受控数据代理分数，不是P01或现实老年人的跌倒概率。",
            "原始压缩包、设备信息和绝对采集时间不进入GitHub。",
        ],
    }
    catalog_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="导入双CSV嵌套压缩包并生成去标识化自主采集工程验证报告。")
    parser.add_argument("archive", type=Path, help="包含 Pxx-动作-序号.zip 的外层压缩包")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()
    report = import_archive(args.archive, args.output_root)
    print(
        json.dumps(
            {
                "received": report["scope"]["received_case_count"],
                "accepted": report["scope"]["accepted_case_count"],
                "rejected": report["scope"]["rejected_case_count"],
                "full_pipeline": report["engineering_results"]["full_three_model_pipeline_case_count"],
                "fall_candidates": report["engineering_results"]["fall_candidate_case_count"],
                "manual_review": report["engineering_results"]["manual_review_case_count"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
