"""导入手表（M5StickS3）串口采集记录。

读取 tools/watch_recorder.py 生成的 CSV（time_s,ax,ay,az,gx,gy,gz，m/s² 与 rad/s），
统一到 50 Hz 后运行三个研究模型，登记到 data/catalog/watch_collected_v1.json。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

from research.early_risk.common import PROJECT_ROOT
from research.early_risk.upload_analysis import analyze_normalized_imu


TARGET_RATE_HZ = 50.0
MINIMUM_DURATION_S = 20.0
EXPECTED_HEADER = ("time_s", "ax", "ay", "az", "gx", "gy", "gz")
REGISTRY_PATH = PROJECT_ROOT / "data" / "catalog" / "watch_collected_v1.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "early_risk" / "watch_collected_v1.json"
OUTPUT_DIR_RELATIVE = Path("data") / "cases" / "watch_m5sticks3_v1"
CASE_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_recording(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("采集文件不是 UTF-8 文本。") from exc
    reader = csv.reader(io.StringIO(text))
    try:
        header = tuple(next(reader))
    except StopIteration as exc:
        raise ValueError("采集文件为空。") from exc
    if header != EXPECTED_HEADER:
        raise ValueError(f"表头必须为 {','.join(EXPECTED_HEADER)}，实际为 {header}")
    rows: list[list[float]] = []
    for row_number, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(row) != 7:
            raise ValueError(f"采集文件第 {row_number} 行不是七列。")
        try:
            rows.append([float(value) for value in row])
        except ValueError as exc:
            raise ValueError(f"采集文件第 {row_number} 行包含非数字。") from exc
    values = np.asarray(rows, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] != 7 or len(values) < 100:
        raise ValueError("采集文件有效采样不足。")
    if not np.isfinite(values).all():
        raise ValueError("采集文件包含无效数值。")
    times = values[:, 0]
    if np.any(np.diff(times) <= 0):
        raise ValueError("时间列必须严格递增。")
    duration_s = float(times[-1] - times[0])
    if duration_s < MINIMUM_DURATION_S:
        raise ValueError(
            f"记录时长 {duration_s:.1f} 秒，不足 {MINIMUM_DURATION_S:.0f} 秒，"
            "不能完整运行三个模型。"
        )
    deltas = np.diff(times)
    rate = 1.0 / float(np.median(deltas))
    if not 10.0 <= rate <= 200.0:
        raise ValueError(f"实测采样率 {rate:.1f} Hz 超出可接受范围。")
    max_gap_ms = float(np.max(deltas)) * 1000.0
    flags: list[str] = []
    if max_gap_ms > 50.0:
        flags.append(f"原始记录最大间隔为 {max_gap_ms:.1f} 毫秒")
    source_metrics = {
        "source_sample_count": int(len(times)),
        "source_rate_hz": round(rate, 3),
        "max_source_gap_ms": round(max_gap_ms, 3),
        "flags": flags,
    }
    return times, values[:, 1:], source_metrics


def _normalize(
    times: np.ndarray, sensors: np.ndarray, source_metrics: dict[str, Any]
) -> tuple[np.ndarray, dict[str, Any]]:
    start = float(times[0])
    end = float(times[-1])
    sample_count = int(np.floor((end - start) * TARGET_RATE_HZ)) + 1
    target_times = start + np.arange(sample_count, dtype=np.float64) / TARGET_RATE_HZ
    normalized = np.column_stack(
        [np.interp(target_times, times, sensors[:, axis]) for axis in range(6)]
    ).astype(np.float32)
    if not np.isfinite(normalized).all():
        raise ValueError("对齐后的六轴数据包含无效数值。")
    flags = list(source_metrics["flags"])
    quality = {
        "status": "ACCEPTED",
        "level": "良好" if not flags else "可用，存在提示",
        "flags": flags,
        "source_sample_count": int(source_metrics["source_sample_count"]),
        "source_rate_hz": float(source_metrics["source_rate_hz"]),
        "max_source_gap_ms": float(source_metrics["max_source_gap_ms"]),
        "normalized_sample_count": int(len(normalized)),
        "normalized_rate_hz": TARGET_RATE_HZ,
        "duration_s": round((len(normalized) - 1) / TARGET_RATE_HZ, 3),
    }
    return normalized, quality


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


def _load_registry() -> dict[str, Any]:
    if REGISTRY_PATH.is_file():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        "registry_version": "1.0.0",
        "status": "WATCH_ENGINEERING_TEST",
        "device": "M5StickS3 (ESP32-S3-PICO-1)",
        "firmware": "firmware/m5sticks3_imu_stream",
        "collection_tool": "tools/watch_recorder.py",
        "transport": "USB Serial/JTAG（USB 串口），目标 50 Hz",
        "received_case_count": 0,
        "accepted_case_count": 0,
        "rejected_case_count": 0,
        "cases": [],
        "required_channels": ["ax", "ay", "az", "gx", "gy", "gz"],
        "canonical_sample_rate_hz": TARGET_RATE_HZ,
        "canonical_units": ["m/s^2", "m/s^2", "m/s^2", "rad/s", "rad/s", "rad/s"],
        "note": (
            "M5StickS3 手表通过 USB 串口实际采集的六轴记录；原始单位为 g 与 deg/s，"
            "采集脚本统一换算为 m/s² 与 rad/s 并重采样到 50 Hz。记录用于验证真实设备"
            "采集链路并运行现有研究模型，不代表现实跌倒预测能力。"
        ),
        "limitations": [
            "手表实测记录来自 M5StickS3（ESP32-S3-PICO-1）经 USB 串口采集，"
            "固件与采集脚本分别为 firmware/m5sticks3_imu_stream 与 tools/watch_recorder.py。",
            "参与者编号与动作名称由采集时的操作登记，没有视频或第二标注者进行独立复核。",
            "记录数量有限且属于工程测试，不构成对任何人群的现实风险验证。",
            "1、2、3 秒输出仍是公开受控数据代理研究分数，不是现实跌倒预测；页面不发送任何通知。",
        ],
    }


def _next_case_id(cases: list[dict[str, Any]], participant: str, action_code: str) -> str:
    prefix = f"watch-{participant.lower()}-{action_code.replace('_', '-')}-"
    index = 1 + sum(1 for item in cases if str(item.get("case_id", "")).startswith(prefix))
    return f"{prefix}{index:02d}"


def _build_report(registry: dict[str, Any], imported_on: str) -> dict[str, Any]:
    cases = registry["cases"]
    return {
        "report_id": "watch-collected-engineering-test-v1",
        "status": "COMPLETED",
        "imported_on": imported_on,
        "device": registry["device"],
        "collection_tool": registry["collection_tool"],
        "case_count": len(cases),
        "cases": [
            {
                "case_id": item["case_id"],
                "action_label": item["action_label"],
                "captured_on": item["capture_date"],
                "quality": item["quality"],
                "analysis_summary": item["analysis_summary"],
            }
            for item in cases
        ],
        "claim": (
            f"已登记 {len(cases)} 条由 M5StickS3 手表通过 USB 串口实际采集的六轴记录，"
            "并由当前活动识别、跌倒候选筛查和 1/2/3 秒研究模型完成计算。"
        ),
        "limitations": registry["limitations"],
    }


def import_watch_recording(
    source_csv: Path,
    *,
    participant: str = "PW01",
    action_code: str = "still",
    action_label: str = "静止",
    action_group: str = "device_test",
    expected_meaning: str = "设备静置测试；用于验证手表采集与分析链路",
    captured_on: str | None = None,
    imported_on: str | None = None,
) -> dict[str, Any]:
    captured_on = captured_on or date.today().isoformat()
    imported_on = imported_on or date.today().isoformat()
    source_csv = source_csv.resolve()
    if not source_csv.is_file():
        raise FileNotFoundError(f"找不到采集文件：{source_csv}")

    times, sensors, source_metrics = _read_recording(source_csv)
    normalized, quality = _normalize(times, sensors, source_metrics)

    registry = _load_registry()
    case_id = _next_case_id(registry["cases"], participant, action_code)
    if not CASE_ID_PATTERN.match(case_id):
        raise ValueError(f"案例编号格式无效：{case_id}")

    output_relative_path = OUTPUT_DIR_RELATIVE / f"{case_id}.npy"
    output_path = PROJECT_ROOT / output_relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = _npy_bytes(normalized)
    output_path.write_bytes(content)

    analysis = analyze_normalized_imu(normalized)
    summary = _analysis_summary(analysis)

    source_bytes = source_csv.read_bytes()
    try:
        source_relative = source_csv.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        source_relative = str(source_csv)

    case = {
        "case_id": case_id,
        "participant_id": participant,
        "action_code": action_code,
        "action_label": action_label,
        "action_group": action_group,
        "expected_meaning": expected_meaning,
        "truth_category": "WATCH_SERIAL_RECORDING",
        "reported_label_source": "operator_input",
        "independent_label_verification": False,
        "capture_date": captured_on,
        "source_format": "m5sticks3_serial_csv",
        "source_file": source_relative,
        "source_file_sha256": _sha256_bytes(source_bytes),
        "processed_relative_path": output_relative_path.as_posix(),
        "processed_sha256": _sha256_bytes(content),
        "channels": ["ax", "ay", "az", "gx", "gy", "gz"],
        "sample_rate_hz": TARGET_RATE_HZ,
        "sample_count": int(len(normalized)),
        "duration_ms": int(round((len(normalized) - 1) * 1000 / TARGET_RATE_HZ)),
        "quality": quality,
        "analysis_summary": summary,
    }

    registry["cases"] = [
        item for item in registry["cases"] if item.get("case_id") != case_id
    ] + [case]
    registry["cases"].sort(key=lambda item: item["case_id"])
    registry["received_case_count"] = len(registry["cases"])
    registry["accepted_case_count"] = len(registry["cases"])
    registry["rejected_case_count"] = 0
    registry["updated_on"] = imported_on
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = _build_report(registry, imported_on)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "status": report["status"],
        "case_id": case_id,
        "case_count": report["case_count"],
        "registry": str(REGISTRY_PATH.relative_to(PROJECT_ROOT)),
        "report": str(REPORT_PATH.relative_to(PROJECT_ROOT)),
        "fall_screening": summary["fall_screening"],
        "activity_label": summary["activity_label"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="导入手表（M5StickS3）串口采集记录。")
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("--participant", default="PW01")
    parser.add_argument("--action-code", default="still")
    parser.add_argument("--action-label", default="静止")
    parser.add_argument("--action-group", default="device_test")
    parser.add_argument(
        "--expected-meaning",
        default="设备静置测试；用于验证手表采集与分析链路",
    )
    parser.add_argument("--captured-on", default=None)
    parser.add_argument("--imported-on", default=None)
    args = parser.parse_args()

    result = import_watch_recording(
        args.source_csv,
        participant=args.participant,
        action_code=args.action_code,
        action_label=args.action_label,
        action_group=args.action_group,
        expected_meaning=args.expected_meaning,
        captured_on=args.captured_on,
        imported_on=args.imported_on,
    )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
