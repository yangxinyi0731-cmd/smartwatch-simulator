from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from backend.app.models.activity import ActivityModelAdapter
from backend.app.models.fall import FallModelAdapter
from backend.app.models.fall_evaluation import SAMPLE_RATE_HZ, WINDOW_SAMPLES, make_windows
from backend.app.training.activity import LABELS, TARGET_RATE_HZ, TARGET_WINDOW_SAMPLES
from research.early_risk.common import PROJECT_ROOT, sha256_file
from research.early_risk.public_risk_model import (
    CONTEXT_SAMPLES,
    HORIZONS_SECONDS,
    PublicEarlyRiskModel,
    risk_points_as_dicts,
)


MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_ROWS = 300_000
NORMALIZED_RATE_HZ = 50.0
FALL_MANIFEST_PATH = PROJECT_ROOT / "models" / "fall_detector" / "tcn_final_candidate" / "manifest.json"
ACTIVITY_MANIFEST_PATH = PROJECT_ROOT / "models" / "activity_recognition" / "capture24_linear_v1" / "manifest.json"
RISK_MODEL_PATH = PROJECT_ROOT / "models" / "early_risk" / "public_weda_linear_v1" / "model.json"
RISK_MANIFEST_PATH = RISK_MODEL_PATH.with_name("manifest.json")
RISK_REPORT_PATH = PROJECT_ROOT / "reports" / "early_risk" / "public_weda_linear_v1.json"
CANONICAL_COLUMNS = ("time_s", "ax", "ay", "az", "gx", "gy", "gz")


ACTIVITY_LABELS_ZH = {
    "walking": "走路候选",
    "eating_candidate": "进食动作候选",
    "sleep_or_lying_candidate": "睡眠或躺卧候选",
    "other_unknown": "其他或暂时无法归类",
}


ANALYSIS_PIPELINE_LABELS = {
    "validate": "检查输入数据",
    "normalize": "统一数据标准",
    "activity": "识别动作或规律",
    "fall": "筛查跌倒动作",
    "risk": "分析提前风险",
    "explain": "生成结果分析",
}


def build_analysis_pipeline(
    *,
    validation: tuple[str, str],
    normalization: tuple[str, str],
    activity: tuple[str, str],
    fall: tuple[str, str],
    risk: tuple[str, str],
    explanation: tuple[str, str] = ("COMPLETED", "已按统一格式生成结论、依据和适用边界。"),
) -> list[dict[str, str]]:
    """Build the one canonical six-step pipeline used by every data source."""

    states = {
        "validate": validation,
        "normalize": normalization,
        "activity": activity,
        "fall": fall,
        "risk": risk,
        "explain": explanation,
    }
    return [
        {
            "id": step_id,
            "label": ANALYSIS_PIPELINE_LABELS[step_id],
            "status": states[step_id][0],
            "detail": states[step_id][1],
        }
        for step_id in ANALYSIS_PIPELINE_LABELS
    ]


@dataclass(frozen=True)
class ParsedRecord:
    times_s: np.ndarray
    values: np.ndarray
    source_format: str
    acceleration_unit: str
    gyroscope_unit: str


def _decode_csv(content: bytes, acceleration_unit: str, gyroscope_unit: str) -> ParsedRecord:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV 必须使用 UTF-8 编码。") from exc
    data_lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not data_lines:
        raise ValueError("CSV 没有可读取的数据。")
    reader = csv.DictReader(io.StringIO("\n".join(data_lines)))
    if reader.fieldnames is None:
        raise ValueError("CSV 缺少表头。")
    normalized_headers = tuple(str(name).strip().lower() for name in reader.fieldnames)
    if normalized_headers != CANONICAL_COLUMNS:
        raise ValueError("CSV 表头必须依次为 time_s,ax,ay,az,gx,gy,gz。")
    times: list[float] = []
    rows: list[list[float]] = []
    for row_number, row in enumerate(reader, start=2):
        if len(times) >= MAX_ROWS:
            raise ValueError(f"单个文件最多允许 {MAX_ROWS:,} 行采样。")
        try:
            times.append(float(row["time_s"] or ""))
            rows.append([float(row[channel] or "") for channel in CANONICAL_COLUMNS[1:]])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"CSV 第 {row_number} 行包含空值或非数字。") from exc
    return ParsedRecord(
        times_s=np.asarray(times, dtype=np.float64),
        values=np.asarray(rows, dtype=np.float64),
        source_format="canonical_csv_v1",
        acceleration_unit=acceleration_unit,
        gyroscope_unit=gyroscope_unit,
    )


def _decode_json(content: bytes, acceleration_unit: str, gyroscope_unit: str) -> ParsedRecord:
    try:
        payload = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON 文件无法解析。") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("samples"), list):
        raise ValueError("JSON 顶层必须包含 samples 数组。")
    samples = payload["samples"]
    if len(samples) > MAX_ROWS:
        raise ValueError(f"单个文件最多允许 {MAX_ROWS:,} 行采样。")
    if not samples or any(not isinstance(row, list) or len(row) != 7 for row in samples):
        raise ValueError("JSON 的每个 samples 项必须是 [time_s,ax,ay,az,gx,gy,gz]。")
    try:
        matrix = np.asarray(samples, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("JSON samples 只能包含数字。") from exc
    units = payload.get("units")
    if isinstance(units, dict):
        acceleration_unit = str(units.get("acceleration", acceleration_unit))
        gyroscope_unit = str(units.get("gyroscope", gyroscope_unit))
    return ParsedRecord(
        times_s=matrix[:, 0],
        values=matrix[:, 1:],
        source_format="canonical_json_v1",
        acceleration_unit=acceleration_unit,
        gyroscope_unit=gyroscope_unit,
    )


def parse_record(
    *, file_name: str, content: bytes, acceleration_unit: str, gyroscope_unit: str
) -> ParsedRecord:
    if not file_name or len(file_name) > 180 or Path(file_name).name != file_name:
        raise ValueError("文件名无效。")
    if not content:
        raise ValueError("所选文件为空。")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("文件超过 5 MB 上限。")
    suffix = Path(file_name).suffix.lower()
    if suffix == ".csv":
        return _decode_csv(content, acceleration_unit, gyroscope_unit)
    if suffix == ".json":
        return _decode_json(content, acceleration_unit, gyroscope_unit)
    raise ValueError("首版只接受标准 CSV 或 JSON 传感器文件。")


def normalize_record(record: ParsedRecord) -> tuple[np.ndarray, dict[str, Any]]:
    times = np.asarray(record.times_s, dtype=np.float64)
    values = np.asarray(record.values, dtype=np.float64)
    if times.ndim != 1 or values.shape != (len(times), 6):
        raise ValueError("传感器记录必须包含时间和六轴数值。")
    if len(times) < CONTEXT_SAMPLES:
        raise ValueError("至少需要 50 个连续六轴采样点，才能运行 1 秒研究窗口。")
    if not np.isfinite(times).all() or not np.isfinite(values).all():
        raise ValueError("传感器文件不能包含 NaN 或无穷值。")

    order = np.argsort(times, kind="stable")
    order_corrected = not np.array_equal(order, np.arange(len(times)))
    times = times[order]
    values = values[order]
    unique_times, unique_indices = np.unique(times, return_index=True)
    duplicate_count = len(times) - len(unique_times)
    times = unique_times
    values = values[unique_indices]
    if len(times) < CONTEXT_SAMPLES:
        raise ValueError("去除重复时间后不足 50 个采样点。")
    times = times - times[0]
    deltas = np.diff(times)
    if np.any(deltas <= 0):
        raise ValueError("时间列必须能整理为严格递增序列。")
    median_delta = float(np.median(deltas))
    source_rate_hz = 1.0 / median_delta
    if not 5.0 <= source_rate_hz <= 400.0:
        raise ValueError("推算采样率必须位于 5–400 Hz。")
    duration_s = float(times[-1])
    if duration_s < 0.98:
        raise ValueError("记录时长不足 1 秒，无法运行提前风险模型。")

    acceleration_units = {"m/s2": 1.0, "m/s^2": 1.0, "g": 9.80665}
    gyroscope_units = {"rad/s": 1.0, "deg/s": np.pi / 180.0, "degree/s": np.pi / 180.0}
    if record.acceleration_unit not in acceleration_units:
        raise ValueError("加速度单位只支持 m/s² 或 g。")
    if record.gyroscope_unit not in gyroscope_units:
        raise ValueError("角速度单位只支持 rad/s 或 deg/s。")
    values = values.copy()
    values[:, :3] *= acceleration_units[record.acceleration_unit]
    values[:, 3:] *= gyroscope_units[record.gyroscope_unit]

    target_times = np.arange(0.0, duration_s + 1e-9, 1.0 / NORMALIZED_RATE_HZ)
    normalized = np.column_stack(
        [np.interp(target_times, times, values[:, channel]) for channel in range(6)]
    ).astype(np.float32)
    if len(normalized) < CONTEXT_SAMPLES:
        raise ValueError("重采样后不足 50 个采样点。")

    max_gap_ms = float(np.max(deltas) * 1000)
    flags: list[str] = []
    if order_corrected:
        flags.append("原始时间顺序已整理")
    if duplicate_count:
        flags.append(f"移除 {duplicate_count} 个重复时间点")
    if max_gap_ms > max(100.0, 5 * median_delta * 1000):
        flags.append(f"原始记录存在 {max_gap_ms:.0f} ms 最大间隔")
    if source_rate_hz < 20:
        flags.append("原始采样率低于 20 Hz，细节可能不足")
    quality_level = "良好" if not flags else "可用，存在提示"
    return normalized, {
        "level": quality_level,
        "flags": flags,
        "source_sample_count": len(record.times_s),
        "normalized_sample_count": len(normalized),
        "source_rate_hz": round(source_rate_hz, 3),
        "normalized_rate_hz": NORMALIZED_RATE_HZ,
        "duration_s": round((len(normalized) - 1) / NORMALIZED_RATE_HZ, 3),
        "max_source_gap_ms": round(max_gap_ms, 3),
        "acceleration_unit_normalized_to": "m/s²",
        "gyroscope_unit_normalized_to": "rad/s",
    }


def _activity_analysis(values_50hz: np.ndarray) -> dict[str, Any]:
    duration_s = (len(values_50hz) - 1) / NORMALIZED_RATE_HZ
    if duration_s < 20.0:
        return {
            "status": "INSUFFICIENT_DURATION",
            "label": "数据不足，未运行活动识别",
            "detail": f"活动识别需要连续 20 秒；本段为 {duration_s:.1f} 秒。",
            "probabilities": None,
            "model_id": None,
        }
    source_times = np.arange(len(values_50hz)) / NORMALIZED_RATE_HZ
    target_times = np.arange(0.0, duration_s + 1e-9, 1.0 / TARGET_RATE_HZ)
    acceleration_20hz = np.column_stack(
        [np.interp(target_times, source_times, values_50hz[:, channel]) for channel in range(3)]
    ).astype(np.float32)
    starts = list(range(0, len(acceleration_20hz) - TARGET_WINDOW_SAMPLES + 1, TARGET_WINDOW_SAMPLES // 2))
    if not starts:
        return {
            "status": "INSUFFICIENT_DURATION",
            "label": "数据不足，未运行活动识别",
            "detail": "重采样后不足一个 20 秒活动窗口。",
            "probabilities": None,
            "model_id": None,
        }
    windows = np.stack([acceleration_20hz[start : start + TARGET_WINDOW_SAMPLES] for start in starts])
    adapter = ActivityModelAdapter(project_root=PROJECT_ROOT, manifest_path=ACTIVITY_MANIFEST_PATH)
    probabilities = adapter.predict_probabilities(windows).mean(axis=0)
    index = int(np.argmax(probabilities))
    label = LABELS[index]
    return {
        "status": "COMPLETED",
        "label": ACTIVITY_LABELS_ZH[label],
        "label_code": label,
        "window_count": len(windows),
        "probabilities": {code: round(float(value), 6) for code, value in zip(LABELS, probabilities, strict=True)},
        "model_id": adapter.manifest.manifest_id,
        "detail": "活动名称是模型候选，需要结合场景确认。",
    }


def _fall_analysis(values_50hz: np.ndarray) -> dict[str, Any]:
    adapter = FallModelAdapter(project_root=PROJECT_ROOT, manifest_path=FALL_MANIFEST_PATH)
    windows, starts = make_windows(values_50hz)
    if len(windows) == 0:
        return {
            "status": "INSUFFICIENT_DURATION",
            "screening": "数据不足，未运行跌倒动作筛查",
            "detail": "跌倒动作模型需要连续 4 秒六轴数据。",
            "window_count": 0,
            "max_score": None,
            "threshold": adapter.threshold,
            "candidate_windows": [],
            "model_id": adapter.manifest.manifest_id,
        }
    probabilities = adapter.predict_fall_probability(windows)
    candidates = [
        {
            "start_offset_ms": int(round(start * 1000 / SAMPLE_RATE_HZ)),
            "end_offset_ms": int(round((start + WINDOW_SAMPLES) * 1000 / SAMPLE_RATE_HZ)),
            "score": round(float(score), 6),
        }
        for start, score in zip(starts, probabilities, strict=True)
        if score >= adapter.threshold
    ]
    return {
        "status": "COMPLETED",
        "screening": "发现跌倒候选" if candidates else "未发现明显跌倒候选",
        "detail": "该分数表示与受控模拟跌倒窗口的特征匹配程度，不是现实跌倒概率。",
        "window_count": len(windows),
        "max_score": round(float(np.max(probabilities)), 6),
        "threshold": adapter.threshold,
        "candidate_windows": candidates,
        "model_id": adapter.manifest.manifest_id,
    }


def _risk_analysis(values_50hz: np.ndarray) -> dict[str, Any]:
    adapter = PublicEarlyRiskModel(RISK_MODEL_PATH)
    points = adapter.predict_timeline(values_50hz)
    if not points:
        return {
            "status": "INSUFFICIENT_DURATION",
            "timeline": [],
            "thresholds": {str(h): round(float(t), 6) for h, t in zip(HORIZONS_SECONDS, adapter.thresholds, strict=True)},
            "max_scores": None,
            "model_id": adapter.model_id,
        }
    matrix = np.asarray([[point.risk_1s, point.risk_2s, point.risk_3s] for point in points])
    return {
        "status": "COMPLETED",
        "timeline": risk_points_as_dicts(points),
        "thresholds": {str(h): round(float(t), 6) for h, t in zip(HORIZONS_SECONDS, adapter.thresholds, strict=True)},
        "max_scores": {str(h): round(float(np.max(matrix[:, index])), 6) for index, h in enumerate(HORIZONS_SECONDS)},
        "attention_detected": {str(h): bool(np.any(matrix[:, index] >= adapter.thresholds[index])) for index, h in enumerate(HORIZONS_SECONDS)},
        "model_id": adapter.model_id,
        "proxy_anchor": adapter.proxy_anchor,
        "meaning": "公开受控数据代理标签的研究分数，不是现实个人跌倒概率。",
    }


def _evidence_and_conclusion(
    values: np.ndarray, activity: dict[str, Any], fall: dict[str, Any], risk: dict[str, Any]
) -> dict[str, Any]:
    acceleration = np.linalg.norm(values[:, :3], axis=1)
    rotation = np.linalg.norm(values[:, 3:], axis=1)
    acceleration_peak_index = int(np.argmax(acceleration))
    acceleration_peak = float(acceleration[acceleration_peak_index])
    rotation_peak = float(np.max(rotation))
    acceleration_baseline = float(np.median(acceleration))
    acceleration_spread = float(np.std(acceleration))
    rotation_baseline = float(np.median(rotation))
    rotation_spread = float(np.std(rotation))
    impact_present = acceleration_peak >= max(18.0, acceleration_baseline + 4 * acceleration_spread)
    rotation_present = rotation_peak >= max(3.0, rotation_baseline + 4 * rotation_spread)
    after = values[acceleration_peak_index + 1 : acceleration_peak_index + 1 + int(NORMALIZED_RATE_HZ)]
    post_stable = bool(
        len(after) >= int(NORMALIZED_RATE_HZ * 0.4)
        and float(np.std(np.linalg.norm(after[:, :3], axis=1))) < 1.5
        and float(np.mean(np.linalg.norm(after[:, 3:], axis=1))) < 1.2
    )
    fall_found = fall["status"] == "COMPLETED" and bool(fall["candidate_windows"])
    risk_attention = bool(
        risk.get("attention_detected") and any(risk["attention_detected"].values())
    )
    review = not fall_found and ((impact_present and rotation_present) or risk_attention)

    evidence = [
        f"六轴数据已统一为 50 Hz、m/s² 和 rad/s，共 {len(values)} 个采样点。",
        f"加速度合量峰值为 {acceleration_peak:.2f} m/s²；腕部角速度合量峰值为 {rotation_peak:.2f} rad/s。",
    ]
    if fall["status"] == "COMPLETED":
        evidence.append(
            f"跌倒动作模型检查 {fall['window_count']} 个 4 秒窗口，最高特征匹配度为 {fall['max_score']:.3f}，关注阈值为 {fall['threshold']:.2f}。"
        )
    else:
        evidence.append(fall["detail"])
    if risk["status"] == "COMPLETED":
        maxima = risk["max_scores"]
        evidence.append(
            f"公开数据提前风险基线的最高研究分数：1 秒 {maxima['1']:.3f}、2 秒 {maxima['2']:.3f}、3 秒 {maxima['3']:.3f}。"
        )
    if post_stable:
        evidence.append("最强加速度变化后，后续约 1 秒腕部运动较快恢复稳定。")
    elif acceleration_peak_index < len(values) - 5:
        evidence.append("最强加速度变化后仍存在连续运动，没有把单个峰值单独当成最终结论。")

    if fall_found:
        current_action = "明显失稳与撞击动作"
        conclusion = "本段记录被筛查为跌倒候选，需要结合动作场景和人工标注进一步确认。"
    elif review:
        current_action = "快速姿态变化"
        conclusion = "本段存在值得复核的快速变化，但现有依据不足以直接判为跌倒；它也可能是快速坐下等日常动作。"
    else:
        current_action = activity["label"] if activity["status"] == "COMPLETED" else "连续腕部动作"
        conclusion = "本段动作更接近日常活动；当前没有发现达到跌倒动作筛查条件的窗口。"

    if risk["status"] == "COMPLETED":
        attention_horizons = [
            f"{horizon} 秒"
            for horizon in HORIZONS_SECONDS
            if risk["attention_detected"].get(str(horizon), False)
        ]
        risk_screening = (
            f"{ '、'.join(attention_horizons) }代理分数达到各自复核线"
            if attention_horizons
            else "1、2、3 秒代理分数均未达到各自复核线"
        )
    else:
        risk_screening = "数据时长不足，未运行提前风险模型"

    if activity["status"] == "COMPLETED":
        activity_score = activity["probabilities"][activity["label_code"]]
        activity_finding = (
            f"在四类日常动作中，{activity['label']}的模型输出值最高（{activity_score:.3f}）；"
            "它只用于说明动作背景。"
        )
    else:
        activity_finding = f"{activity['detail']} 因此本次结论不依赖活动类别。"

    if fall["status"] == "COMPLETED":
        candidate_count = len(fall["candidate_windows"])
        fall_finding = (
            f"共检查 {fall['window_count']} 个连续 4 秒六轴窗口，最高特征匹配度 "
            f"{fall['max_score']:.3f}，关注阈值 {fall['threshold']:.2f}；"
            f"{f'有 {candidate_count} 个窗口达到筛查条件' if candidate_count else '没有窗口达到筛查条件'}。"
        )
    else:
        fall_finding = fall["detail"]

    if risk["status"] == "COMPLETED":
        maxima = risk["max_scores"]
        risk_finding = (
            f"逐秒计算公开数据代理分数，最高值依次为：1 秒 {maxima['1']:.3f}、"
            f"2 秒 {maxima['2']:.3f}、3 秒 {maxima['3']:.3f}；{risk_screening}。"
        )
    else:
        risk_finding = "连续记录不足以形成提前风险时间线，本次不提供 1、2、3 秒结果。"

    if fall_found:
        synthesis_finding = "跌倒模型达到筛查条件，且波形同时出现明显加速度与转动变化，因此列为跌倒候选。"
    elif review:
        synthesis_finding = "跌倒模型未形成明确候选，但波形或提前风险代理分数出现关注线索，因此保留人工复核。"
    else:
        synthesis_finding = "跌倒模型未达到筛查条件，波形交叉核对也没有形成足够的失稳证据，因此更接近日常活动。"

    model_reasoning = [
        {
            "model": "活动识别模型",
            "plain_name": "判断这段连续动作更像哪一种日常活动",
            "status": activity["status"],
            "finding": activity_finding,
            "role": "提供动作背景，不单独决定是否跌倒。",
        },
        {
            "model": "跌倒动作模型",
            "plain_name": "在连续六轴窗口中筛查失稳与撞击动作",
            "status": fall["status"],
            "finding": fall_finding,
            "role": "决定是否形成跌倒候选，是本次动作筛查的主要模型。",
        },
        {
            "model": "提前风险模型",
            "plain_name": "逐秒检查未来 1、2、3 秒代理风险线索",
            "status": risk["status"],
            "finding": risk_finding,
            "role": "只提供复核线索，不等同于现实跌倒概率。",
        },
    ]
    return {
        "current_activity": current_action,
        "fall_screening": fall["screening"],
        "risk_screening": risk_screening,
        "evidence": evidence,
        "model_reasoning": model_reasoning,
        "decision_rule": "三个模型的分数不会相加成一个“综合风险分”。系统先看跌倒候选，再用实际波形、动作背景和提前风险线索交叉核对。",
        "synthesis": synthesis_finding,
        "conclusion": conclusion,
        "scope_note": "本结果来自公开受控数据研究模型，只用于校赛演示和工程验证；不是医学诊断、现实报警或已验证的个人跌倒概率。",
        "review_required": fall_found or review,
        "measured_facts": {
            "acceleration_peak_m_s2": round(acceleration_peak, 6),
            "angular_velocity_peak_rad_s": round(rotation_peak, 6),
            "impact_pattern_present": impact_present,
            "rotation_pattern_present": rotation_present,
            "post_change_stabilized": post_stable,
        },
    }


def _waveform(values: np.ndarray, max_points: int = 360) -> dict[str, Any]:
    stride = max(1, int(np.ceil(len(values) / max_points)))
    acceleration = np.linalg.norm(values[:, :3], axis=1)
    rotation = np.linalg.norm(values[:, 3:], axis=1)
    indices = sorted({
        *range(0, len(values), stride),
        len(values) - 1,
        int(np.argmax(acceleration)),
        int(np.argmax(rotation)),
    })
    return {
        "displayed_point_count": len(indices),
        "acceleration_magnitude": [
            [int(round(index * 1000 / NORMALIZED_RATE_HZ)), round(float(acceleration[index]), 6)] for index in indices
        ],
        "angular_velocity_magnitude": [
            [int(round(index * 1000 / NORMALIZED_RATE_HZ)), round(float(rotation[index]), 6)] for index in indices
        ],
    }


def analyze_normalized_imu(values_50hz: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values_50hz, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 6 or len(values) < CONTEXT_SAMPLES:
        raise ValueError("模型分析需要至少 50 个标准六轴采样点。")
    if not np.isfinite(values).all():
        raise ValueError("模型分析输入不能包含 NaN 或无穷值。")
    activity = _activity_analysis(values)
    fall = _fall_analysis(values)
    risk = _risk_analysis(values)
    interpretation = _evidence_and_conclusion(values, activity, fall, risk)
    return {
        "activity_model": activity,
        "fall_model": fall,
        "early_risk_model": risk,
        "interpretation": interpretation,
        "waveform": _waveform(values),
    }


def analyze_upload_request(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"file_name", "content_base64", "acceleration_unit", "gyroscope_unit"}
    extras = sorted(set(payload) - allowed)
    if extras:
        raise ValueError(f"不支持的上传字段：{', '.join(extras)}")
    file_name = payload.get("file_name")
    encoded = payload.get("content_base64")
    if not isinstance(file_name, str) or not isinstance(encoded, str):
        raise ValueError("上传请求必须包含文件名和 Base64 内容。")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("文件内容不是有效 Base64。") from exc
    acceleration_unit = str(payload.get("acceleration_unit", "m/s2"))
    gyroscope_unit = str(payload.get("gyroscope_unit", "rad/s"))
    parsed = parse_record(
        file_name=file_name,
        content=content,
        acceleration_unit=acceleration_unit,
        gyroscope_unit=gyroscope_unit,
    )
    normalized, quality = normalize_record(parsed)
    analysis = analyze_normalized_imu(normalized)
    return {
        "analysis_id": f"local-{hashlib.sha256(content).hexdigest()[:12]}",
        "file": {
            "name": file_name,
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "source_format": parsed.source_format,
            "persisted": False,
        },
        "pipeline": build_analysis_pipeline(
            validation=("COMPLETED", f"已读取 {len(parsed.values)} 个六轴采样点，加速度和陀螺仪齐全。"),
            normalization=(
                "COMPLETED",
                f"已统一为 50 Hz、m/s² 和 rad/s，共 {len(normalized)} 个标准采样点。",
            ),
            activity=(analysis["activity_model"]["status"], analysis["activity_model"]["detail"]),
            fall=(analysis["fall_model"]["status"], analysis["fall_model"]["detail"]),
            risk=(
                analysis["early_risk_model"]["status"],
                analysis["interpretation"]["risk_screening"],
            ),
        ),
        "quality": quality,
        "analysis": analysis,
        "traceability": {
            "fall_manifest_sha256": sha256_file(FALL_MANIFEST_PATH),
            "activity_manifest_sha256": sha256_file(ACTIVITY_MANIFEST_PATH),
            "early_risk_manifest_sha256": sha256_file(RISK_MANIFEST_PATH),
            "early_risk_report_sha256": sha256_file(RISK_REPORT_PATH),
        },
        "truth_boundary": {
            "public_proxy_model_ready": True,
            "self_collected_validation_complete": False,
            "real_world_prediction_evidence": False,
            "deployment_approved": False,
            "external_notification_sent": False,
            "notice": "文件仅在内存中分析，不保存；输出是校赛研究结果，不是医学诊断或现实报警。",
        },
    }
