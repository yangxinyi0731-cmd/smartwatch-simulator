from __future__ import annotations

import hashlib
from collections import defaultdict
from datetime import UTC, datetime
from math import ceil
from pathlib import Path

import numpy as np

from .contracts import ActivityProbabilities, ModelKind
from .database import CaseRuntimeBundle
from .models.activity import ActivityModelAdapter
from .models.fall import FallModelAdapter
from .models.fall_evaluation import SAMPLE_RATE_HZ, WINDOW_SAMPLES, make_windows, merge_alarm_windows
from .models.routine import RoutineModelAdapter
from .schemas import (
    FallAlarmEpisodeItem,
    FallWindowResult,
    ActivityPreviewResult,
    ReplayPreviewResponse,
    RoutineDayResult,
    RoutineProfileSummary,
    SensorSamplePoint,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FALL_MANIFEST_PATH = PROJECT_ROOT / "models/fall_detector/tcn_final_candidate/manifest.json"
ROUTINE_MANIFEST_PATH = PROJECT_ROOT / "models/routine_anomaly/statistical_v1/manifest.json"
ACTIVITY_MANIFEST_PATH = PROJECT_ROOT / "models/activity_recognition/capture24_linear_v1/manifest.json"
MAX_SENSOR_POINTS = 900


def _load_sensor_array(bundle: CaseRuntimeBundle) -> tuple[np.ndarray, object] | None:
    if not bundle.streams:
        return None
    if len(bundle.streams) != 1:
        raise ValueError("首版回放只接受每案例一条已登记传感器流。")
    stream = bundle.streams[0]
    path = (PROJECT_ROOT / stream.relative_path).resolve()
    if PROJECT_ROOT not in path.parents:
        raise ValueError("传感器文件必须位于项目目录内。")
    if not path.is_file():
        raise FileNotFoundError("案例登记的本地传感器文件不存在。")
    if hashlib.sha256(path.read_bytes()).hexdigest() != stream.content_sha256:
        raise ValueError("案例传感器文件哈希与数据库登记不一致。")
    if stream.storage_format.value != "NPY":
        raise ValueError("首版回放只读取已核验的 NPY 传感器流。")
    values = np.load(path, allow_pickle=False)
    if values.shape != (stream.sample_count, len(stream.channels)):
        raise ValueError("传感器数组形状与数据库登记不一致。")
    if values.dtype != np.float32 or not np.isfinite(values).all():
        raise ValueError("传感器数组必须是有限 float32 数值。")
    return values, stream


def _sensor_points(values: np.ndarray, sample_rate_hz: float) -> tuple[SensorSamplePoint, ...]:
    stride = max(1, ceil(len(values) / MAX_SENSOR_POINTS))
    indices = list(range(0, len(values), stride))
    if indices[-1] != len(values) - 1:
        indices.append(len(values) - 1)
    return tuple(
        SensorSamplePoint(
            offset_ms=int(round(index * 1000 / sample_rate_hz)),
            values=tuple(float(value) for value in values[index]),
        )
        for index in indices
    )


def _fall_results(values: np.ndarray) -> tuple[str, float, tuple[FallWindowResult, ...], tuple[FallAlarmEpisodeItem, ...]]:
    adapter = FallModelAdapter(project_root=PROJECT_ROOT, manifest_path=FALL_MANIFEST_PATH)
    windows, starts = make_windows(values)
    if len(windows) == 0:
        return adapter.manifest.manifest_id, adapter.threshold, (), ()
    probabilities = adapter.predict_fall_probability(windows)
    threshold = adapter.threshold
    results = tuple(
        FallWindowResult(
            start_offset_ms=int(round(start * 1000 / SAMPLE_RATE_HZ)),
            end_offset_ms=int(round((start + WINDOW_SAMPLES) * 1000 / SAMPLE_RATE_HZ)),
            fall_probability=float(probability),
            is_candidate=bool(probability >= threshold),
        )
        for start, probability in zip(starts, probabilities, strict=True)
    )
    episodes = tuple(
        FallAlarmEpisodeItem(
            start_offset_ms=item.start_offset_ms,
            end_offset_ms=item.end_offset_ms,
            peak_probability=item.peak_probability,
            window_count=item.window_count,
        )
        for item in merge_alarm_windows(starts, probabilities, threshold)
    )
    return adapter.manifest.manifest_id, threshold, results, episodes


def _routine_results(bundle: CaseRuntimeBundle) -> tuple[RoutineProfileSummary | None, tuple[RoutineDayResult, ...]]:
    profile = bundle.routine_profile
    if profile is None:
        return None, ()
    adapter = RoutineModelAdapter(
        project_root=PROJECT_ROOT,
        manifest_path=ROUTINE_MANIFEST_PATH,
    )
    by_day = defaultdict(list)
    for event in bundle.routine_events:
        by_day[event.started_at.date()].append(event)
    days = tuple(
        RoutineDayResult(
            day=day,
            events=tuple(by_day[day]),
            assessments=adapter.assess_day(tuple(by_day[day])),
        )
        for day in sorted(by_day)
    )
    return (
        RoutineProfileSummary(
            profile_id=profile.profile_id,
            history_days=profile.history_days,
            history_start=profile.history_start,
            history_end=profile.history_end,
            seed=profile.seed,
            event_count=profile.event_count,
            events_sha256=profile.events_sha256,
        ),
        days,
    )


def _activity_result(values: np.ndarray) -> ActivityPreviewResult:
    from .training.activity import LABELS

    adapter = ActivityModelAdapter(
        project_root=PROJECT_ROOT,
        manifest_path=ACTIVITY_MANIFEST_PATH,
    )
    if values.shape != (400, 3):
        raise ValueError("活动案例传感器数组必须是 [400, 3]。")
    probabilities = adapter.predict_probabilities(values[None, ...])[0]
    prediction_index = int(np.argmax(probabilities))
    return ActivityPreviewResult(
        manifest_id=adapter.manifest.manifest_id,
        probabilities=ActivityProbabilities(
            walking=float(probabilities[0]),
            eating_candidate=float(probabilities[1]),
            sleep_or_lying_candidate=float(probabilities[2]),
            other_unknown=float(probabilities[3]),
        ),
        predicted_label=LABELS[prediction_index],
    )


def build_replay_preview(bundle: CaseRuntimeBundle) -> ReplayPreviewResponse:
    sensor_payload = _load_sensor_array(bundle)
    stream = sensor_payload[1] if sensor_payload is not None else None
    values = sensor_payload[0] if sensor_payload is not None else None
    quality = bundle.qualities[0] if bundle.qualities else None
    duration_ms = stream.duration_ms if stream is not None else 0
    samples = (
        _sensor_points(values, stream.sample_rate_hz)
        if values is not None and stream is not None
        else ()
    )

    fall_manifest_id = None
    fall_threshold = None
    fall_windows: tuple[FallWindowResult, ...] = ()
    fall_episodes: tuple[FallAlarmEpisodeItem, ...] = ()
    if ModelKind.FALL_DETECTION in bundle.case.allowed_models:
        if values is None:
            raise ValueError("跌倒案例缺少已登记的真实六轴传感器流。")
        (
            fall_manifest_id,
            fall_threshold,
            fall_windows,
            fall_episodes,
        ) = _fall_results(values)

    routine_profile, routine_days = _routine_results(bundle)
    activity_result = None
    if ModelKind.ACTIVITY_RECOGNITION in bundle.case.allowed_models:
        if values is None:
            raise ValueError("活动案例缺少已登记的真实三轴传感器流。")
        activity_result = _activity_result(values)
    messages = [
        "所有波形点均来自已登记本地文件；页面不生成随机传感器数据。",
        "三个模型保持独立输出，不生成综合医学风险分数。",
    ]
    if bundle.case.truth_category.value == "SIMULATED_FALL":
        messages.append("本案例是年轻参与者在受控床垫条件下模拟的跌倒，不是真实老人跌倒。")
    if bundle.case.age_group.value == "OLDER_ADULT":
        messages.append("本案例中的老年参与者只执行日常活动，用于观察跌倒模型误报。")
    if quality is not None and quality.flags:
        messages.append("该来源记录存在已保存的数据质量标记，回放时必须同时展示。")
    if routine_profile is not None:
        messages.append("100 天生活规律为固定种子合成事件，不代表真实老人行为。")
    if activity_result is not None:
        messages.append("活动标签来自自由生活注释映射；进食和睡眠或躺卧只表示候选类别。")

    return ReplayPreviewResponse(
        case=bundle.case,
        duration_ms=duration_ms,
        sensor_stream=stream,
        sensor_quality=quality,
        ground_truth_events=bundle.ground_truth_events,
        sensor_samples=samples,
        fall_manifest_id=fall_manifest_id,
        fall_threshold=fall_threshold,
        fall_windows=fall_windows,
        fall_alarm_episodes=fall_episodes,
        routine_profile=routine_profile,
        routine_days=routine_days,
        activity_result=activity_result,
        messages=tuple(messages),
        generated_at=datetime.now(UTC),
    )
