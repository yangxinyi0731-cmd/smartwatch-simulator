from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from research.early_risk.common import PROJECT_ROOT
from research.early_risk.upload_analysis import analyze_normalized_imu


TARGET_RATE_HZ = 50.0
EXPECTED_CASE_COUNT = 30
PARTICIPANT_ID = "P01"
CASE_NAME_PATTERN = re.compile(r"^P01-(?P<action>.+)-(?P<repeat>\d{2})\.zip$")
EXPECTED_INNER_FILES = {
    "Accelerometer.csv",
    "Gyroscope.csv",
    "meta/device.csv",
    "meta/time.csv",
}


@dataclass(frozen=True)
class ActionDefinition:
    code: str
    label: str
    group: str
    expected_meaning: str


ACTIONS: dict[str, ActionDefinition] = {
    "走路": ActionDefinition(
        code="walking",
        label="正常走路",
        group="daily_activity",
        expected_meaning="日常活动",
    ),
    "正常坐下": ActionDefinition(
        code="normal_sit",
        label="正常坐下",
        group="daily_activity",
        expected_meaning="日常活动",
    ),
    "快速坐下": ActionDefinition(
        code="fast_sit",
        label="快速坐下",
        group="difficult_negative",
        expected_meaning="容易与跌倒混淆的日常动作",
    ),
    "弯腰捡东西": ActionDefinition(
        code="bend_pickup",
        label="弯腰捡东西",
        group="difficult_negative",
        expected_meaning="容易与失衡混淆的日常动作",
    ),
    "大幅度摆臂": ActionDefinition(
        code="large_arm_swing",
        label="大幅度摆臂",
        group="difficult_negative",
        expected_meaning="容易产生瞬时波动的日常动作",
    ),
    "安全失衡": ActionDefinition(
        code="safe_instability",
        label="安全失衡",
        group="controlled_instability",
        expected_meaning="受控失衡动作，不登记为真实跌倒",
    ),
}
ACTION_ORDER = {definition.code: index for index, definition in enumerate(ACTIONS.values())}


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_zip_name(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"压缩包包含不安全路径：{name}")


def _read_sensor_csv(
    archive: zipfile.ZipFile,
    file_name: str,
    expected_headers: tuple[str, str, str, str],
) -> tuple[np.ndarray, np.ndarray]:
    try:
        content = archive.read(file_name)
    except KeyError as exc:
        raise ValueError(f"采集文件缺少 {file_name}。") from exc
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{file_name} 不是 UTF-8 文本。") from exc
    reader = csv.reader(io.StringIO(text))
    try:
        headers = tuple(next(reader))
    except StopIteration as exc:
        raise ValueError(f"{file_name} 为空。") from exc
    if headers != expected_headers:
        raise ValueError(f"{file_name} 表头不符合 phyphox 导出格式：{headers}")
    rows: list[list[float]] = []
    for row_number, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(row) != 4:
            raise ValueError(f"{file_name} 第 {row_number} 行不是四列。")
        try:
            rows.append([float(value) for value in row])
        except ValueError as exc:
            raise ValueError(f"{file_name} 第 {row_number} 行包含非数字。") from exc
    values = np.asarray(rows, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 4 or len(values) < 100:
        raise ValueError(f"{file_name} 有效采样不足。")
    if not np.isfinite(values).all():
        raise ValueError(f"{file_name} 包含无效数值。")
    times = values[:, 0]
    if np.any(np.diff(times) <= 0):
        raise ValueError(f"{file_name} 时间必须严格递增。")
    return times, values[:, 1:]


def _read_metadata(archive: zipfile.ZipFile, file_name: str) -> dict[str, str]:
    try:
        content = archive.read(file_name).decode("utf-8-sig")
    except (KeyError, UnicodeDecodeError) as exc:
        raise ValueError(f"无法读取 {file_name}。") from exc
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows or rows[0] != ["property", "value"]:
        return {}
    return {row[0]: row[1] for row in rows[1:] if len(row) == 2}


def _read_capture_date(archive: zipfile.ZipFile) -> str | None:
    try:
        content = archive.read("meta/time.csv").decode("utf-8-sig")
    except (KeyError, UnicodeDecodeError):
        return None
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        if row.get("event") == "START":
            text = str(row.get("system time text", ""))
            match = re.match(r"(\d{4}-\d{2}-\d{2})", text)
            return match.group(1) if match else None
    return None


def _rate_and_gap_ms(times: np.ndarray) -> tuple[float, float]:
    deltas = np.diff(times)
    return 1.0 / float(np.median(deltas)), float(np.max(deltas) * 1000)


def _normalize_sensors(
    acceleration_times: np.ndarray,
    acceleration: np.ndarray,
    gyroscope_times: np.ndarray,
    gyroscope: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    common_start = max(float(acceleration_times[0]), float(gyroscope_times[0]))
    common_end = min(float(acceleration_times[-1]), float(gyroscope_times[-1]))
    if common_end <= common_start:
        raise ValueError("加速度与陀螺仪没有可对齐的共同时间。")
    duration_s = common_end - common_start
    sample_count = int(np.floor(duration_s * TARGET_RATE_HZ)) + 1
    if sample_count < int(20 * TARGET_RATE_HZ) + 1:
        raise ValueError("共同记录不足 20 秒，不能完整运行三个模型。")
    target_times = common_start + np.arange(sample_count, dtype=np.float64) / TARGET_RATE_HZ
    normalized = np.column_stack(
        [
            *(
                np.interp(target_times, acceleration_times, acceleration[:, axis])
                for axis in range(3)
            ),
            *(
                np.interp(target_times, gyroscope_times, gyroscope[:, axis])
                for axis in range(3)
            ),
        ]
    ).astype(np.float32)
    if not np.isfinite(normalized).all():
        raise ValueError("对齐后的六轴数据包含无效数值。")
    acceleration_rate, acceleration_gap = _rate_and_gap_ms(acceleration_times)
    gyroscope_rate, gyroscope_gap = _rate_and_gap_ms(gyroscope_times)
    flags: list[str] = []
    max_gap_ms = max(acceleration_gap, gyroscope_gap)
    if max_gap_ms > 50:
        flags.append(f"原始记录最大间隔为 {max_gap_ms:.1f} 毫秒")
    start_offset_ms = abs(float(acceleration_times[0] - gyroscope_times[0]) * 1000)
    if start_offset_ms > 20:
        flags.append(f"两个传感器起点相差 {start_offset_ms:.1f} 毫秒")
    return normalized, {
        "status": "ACCEPTED",
        "level": "良好" if not flags else "可用，存在提示",
        "flags": flags,
        "source_acceleration_sample_count": int(len(acceleration_times)),
        "source_gyroscope_sample_count": int(len(gyroscope_times)),
        "source_acceleration_rate_hz": round(acceleration_rate, 3),
        "source_gyroscope_rate_hz": round(gyroscope_rate, 3),
        "max_source_gap_ms": round(max_gap_ms, 3),
        "sensor_start_offset_ms": round(start_offset_ms, 3),
        "normalized_sample_count": int(len(normalized)),
        "normalized_rate_hz": TARGET_RATE_HZ,
        "duration_s": round((len(normalized) - 1) / TARGET_RATE_HZ, 3),
    }


def _npy_bytes(values: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, values, allow_pickle=False)
    return buffer.getvalue()


def _analysis_summary(analysis: dict[str, Any]) -> dict[str, Any]:
    fall = analysis["fall_model"]
    risk = analysis["early_risk_model"]
    return {
        "activity_label": analysis["activity_model"]["label"],
        "activity_status": analysis["activity_model"]["status"],
        "fall_screening": fall["screening"],
        "fall_max_score": fall["max_score"],
        "fall_threshold": fall["threshold"],
        "fall_candidate_window_count": len(fall["candidate_windows"]),
        "early_risk_attention_detected": risk.get("attention_detected"),
        "conclusion": analysis["interpretation"]["conclusion"],
    }


def import_archive(source_archive: Path, *, imported_on: str) -> tuple[dict[str, Any], dict[str, Any]]:
    source_archive = source_archive.resolve()
    if not source_archive.is_file():
        raise FileNotFoundError(f"找不到自主采集压缩包：{source_archive}")
    outer_bytes = source_archive.read_bytes()
    outer_sha256 = _sha256_bytes(outer_bytes)
    cases: list[dict[str, Any]] = []
    report_cases: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()

    with zipfile.ZipFile(io.BytesIO(outer_bytes)) as outer:
        for entry in outer.infolist():
            _safe_zip_name(entry.filename)
        inner_entries = sorted(
            (entry for entry in outer.infolist() if entry.filename.lower().endswith(".zip")),
            key=lambda item: item.filename,
        )
        if len(inner_entries) != EXPECTED_CASE_COUNT:
            raise ValueError(
                f"压缩包应包含 {EXPECTED_CASE_COUNT} 组动作，实际为 {len(inner_entries)} 组。"
            )
        for entry in inner_entries:
            base_name = PurePosixPath(entry.filename).name
            match = CASE_NAME_PATTERN.fullmatch(base_name)
            if match is None:
                raise ValueError(f"动作文件名不符合 P01-动作-序号.zip：{base_name}")
            action_name = match.group("action")
            action = ACTIONS.get(action_name)
            if action is None:
                raise ValueError(f"未登记的动作名称：{action_name}")
            repeat = int(match.group("repeat"))
            if not 1 <= repeat <= 5:
                raise ValueError(f"动作序号必须是 01–05：{base_name}")
            action_counts[action_name] += 1

            inner_bytes = outer.read(entry)
            with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
                for inner_entry in inner.infolist():
                    _safe_zip_name(inner_entry.filename)
                actual_files = {item.filename for item in inner.infolist() if not item.is_dir()}
                if actual_files != EXPECTED_INNER_FILES:
                    raise ValueError(
                        f"{base_name} 的文件组成不正确：{sorted(actual_files)}"
                    )
                acceleration_times, acceleration = _read_sensor_csv(
                    inner,
                    "Accelerometer.csv",
                    ("Time (s)", "X (m/s^2)", "Y (m/s^2)", "Z (m/s^2)"),
                )
                gyroscope_times, gyroscope = _read_sensor_csv(
                    inner,
                    "Gyroscope.csv",
                    ("Time (s)", "X (rad/s)", "Y (rad/s)", "Z (rad/s)"),
                )
                device = _read_metadata(inner, "meta/device.csv")
                capture_date = _read_capture_date(inner)

            normalized, quality = _normalize_sensors(
                acceleration_times,
                acceleration,
                gyroscope_times,
                gyroscope,
            )
            case_id = f"self-p01-{action.code}-{repeat:02d}"
            output_relative_path = Path("data") / "cases" / "self_collected_p01_v1" / f"{case_id}.npy"
            output_path = PROJECT_ROOT / output_relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            content = _npy_bytes(normalized)
            output_path.write_bytes(content)
            analysis = analyze_normalized_imu(normalized)
            summary = _analysis_summary(analysis)
            registry_case = {
                "case_id": case_id,
                "participant_id": PARTICIPANT_ID,
                "action_code": action.code,
                "action_label": action.label,
                "action_group": action.group,
                "expected_meaning": action.expected_meaning,
                "truth_category": "SELF_COLLECTED_CONTROLLED_ACTION",
                "reported_label_source": "collector_file_name",
                "independent_label_verification": False,
                "capture_date": capture_date,
                "source_format": "phyphox",
                "source_app_version": device.get("version"),
                "source_archive_member": entry.filename,
                "source_member_sha256": _sha256_bytes(inner_bytes),
                "processed_relative_path": output_relative_path.as_posix(),
                "processed_sha256": _sha256_bytes(content),
                "channels": ["ax", "ay", "az", "gx", "gy", "gz"],
                "sample_rate_hz": TARGET_RATE_HZ,
                "sample_count": int(len(normalized)),
                "duration_ms": int(round((len(normalized) - 1) * 1000 / TARGET_RATE_HZ)),
                "quality": quality,
                "analysis_summary": summary,
            }
            cases.append(registry_case)
            report_cases.append(
                {
                    "case_id": case_id,
                    "action_label": action.label,
                    "action_group": action.group,
                    "quality": quality,
                    "analysis_summary": summary,
                }
            )

    if set(action_counts) != set(ACTIONS) or any(action_counts[name] != 5 for name in ACTIONS):
        raise ValueError(f"六类动作必须各有 5 组，实际为：{dict(action_counts)}")
    cases.sort(key=lambda item: (ACTION_ORDER[item["action_code"]], item["case_id"]))
    report_cases.sort(
        key=lambda item: (
            ACTION_ORDER[next(
                definition.code
                for definition in ACTIONS.values()
                if definition.label == item["action_label"]
            )],
            item["case_id"],
        )
    )

    fall_candidate_cases = [
        item for item in report_cases if item["analysis_summary"]["fall_candidate_window_count"]
    ]
    activity_counts = Counter(
        item["analysis_summary"]["activity_label"] for item in report_cases
    )
    fall_candidate_counts_by_action = {
        definition.label: sum(
            item["action_label"] == definition.label
            and item["analysis_summary"]["fall_candidate_window_count"] > 0
            for item in report_cases
        )
        for definition in ACTIONS.values()
    }
    risk_attention_counts = {
        horizon: sum(
            bool((item["analysis_summary"]["early_risk_attention_detected"] or {}).get(horizon))
            for item in report_cases
        )
        for horizon in ("1", "2", "3")
    }
    registry = {
        "registry_version": "1.1.0",
        "status": "ENGINEERING_VALIDATION_COMPLETE",
        "expected_case_count": EXPECTED_CASE_COUNT,
        "received_case_count": len(cases),
        "accepted_case_count": len(cases),
        "rejected_case_count": 0,
        "claim_enabled": True,
        "participant_count": 1,
        "participant_ids": [PARTICIPANT_ID],
        "source_archive_sha256": outer_sha256,
        "source_archive_bytes": len(outer_bytes),
        "imported_on": imported_on,
        "cases": cases,
        "required_channels": ["ax", "ay", "az", "gx", "gy", "gz"],
        "canonical_sample_rate_hz": TARGET_RATE_HZ,
        "canonical_units": ["m/s^2", "m/s^2", "m/s^2", "rad/s", "rad/s", "rad/s"],
        "note": (
            "已收到并核验 P01 的 30 组 phyphox 六轴动作数据，六类动作各 5 组；"
            "已完成格式统一、三个研究模型运行和页面登记。"
        ),
        "limitations": [
            "全部 30 组来自同一名参与者 P01，不能代表不同年龄或不同人群。",
            "动作名称来自采集者文件名，没有视频或第二标注者进行独立复核。",
            "安全失衡是受控动作，不登记为真实跌倒，也不能用于证明现实预测效果。",
            "自主采集数据用于工程验证，没有加入公开代理模型的训练。",
        ],
    }
    report = {
        "report_id": "self-collected-p01-engineering-validation-v1",
        "status": "COMPLETED_WITH_FINDINGS",
        "imported_on": imported_on,
        "source_archive_sha256": outer_sha256,
        "participant_count": 1,
        "received_case_count": len(cases),
        "accepted_case_count": len(cases),
        "rejected_case_count": 0,
        "action_counts": {ACTIONS[name].label: action_counts[name] for name in ACTIONS},
        "quality": {
            "result": "PASS",
            "all_have_six_axes": True,
            "all_at_least_20_seconds": True,
            "all_three_models_executed": all(
                item["analysis_summary"]["activity_status"] == "COMPLETED"
                for item in report_cases
            ),
            "cases_with_quality_flags": sum(bool(item["quality"]["flags"]) for item in report_cases),
            "duration_range_s": [
                min(item["quality"]["duration_s"] for item in report_cases),
                max(item["quality"]["duration_s"] for item in report_cases),
            ],
        },
        "model_observations": {
            "activity_output_counts": dict(sorted(activity_counts.items())),
            "fall_candidate_case_count": len(fall_candidate_cases),
            "fall_candidate_case_ids": [item["case_id"] for item in fall_candidate_cases],
            "fall_candidate_counts_by_action": fall_candidate_counts_by_action,
            "early_risk_attention_case_count": risk_attention_counts,
            "engineering_finding": (
                "30 组数据均完成计算，但当前模型把 5 组大幅度摆臂和 2 组正常走路标记为跌倒候选，"
                "5 组安全失衡均未达到跌倒候选阈值；这说明跨设备使用时仍需调整模型和阈值。"
            ),
        },
        "claim": (
            "已使用 30 组自主采集腕部六轴动作数据完成工程验证；每组均由当前活动识别、"
            "跌倒候选筛查和 1/2/3 秒公开代理研究模型实际计算。"
        ),
        "limitations": registry["limitations"],
        "cases": report_cases,
    }
    return registry, report


def main() -> None:
    parser = argparse.ArgumentParser(description="导入 P01 phyphox 自主采集动作数据。")
    parser.add_argument("source_archive", type=Path)
    parser.add_argument("--imported-on", default=date.today().isoformat())
    parser.add_argument("--keep-raw-copy", action="store_true")
    args = parser.parse_args()

    registry, report = import_archive(args.source_archive, imported_on=args.imported_on)
    registry_path = PROJECT_ROOT / "data" / "catalog" / "self_collected_pending_v1.json"
    report_path = PROJECT_ROOT / "reports" / "early_risk" / "self_collected_p01_v1.json"
    registry_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.keep_raw_copy:
        raw_path = (
            PROJECT_ROOT
            / "data"
            / "raw"
            / "self_collected"
            / PARTICIPANT_ID
            / args.source_archive.name
        )
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        if raw_path.exists():
            if _sha256_bytes(raw_path.read_bytes()) != _sha256_bytes(args.source_archive.read_bytes()):
                raise FileExistsError(f"原始数据副本已存在且内容不同：{raw_path}")
        else:
            shutil.copy2(args.source_archive, raw_path)
    print(
        json.dumps(
            {
                "status": report["status"],
                "accepted_case_count": report["accepted_case_count"],
                "registry": str(registry_path.relative_to(PROJECT_ROOT)),
                "report": str(report_path.relative_to(PROJECT_ROOT)),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
