from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Iterable, Sequence


class TemporalLeakageError(ValueError):
    pass


class TransformationMode(StrEnum):
    CAUSAL = "CAUSAL"
    NON_CAUSAL = "NON_CAUSAL"


@dataclass(frozen=True, slots=True)
class TimelineSample:
    participant_id: str
    timestamp_ms: int
    values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class PreEventWindow:
    window_id: str
    event_id: str
    participant_id: str
    target_anchor_ms: int
    requested_start_ms: int
    cutoff_ms: int
    transformation_mode: TransformationMode
    samples: tuple[TimelineSample, ...]

    @property
    def source_max_timestamp_ms(self) -> int:
        return max(sample.timestamp_ms for sample in self.samples)


def strict_pre_event_window(
    samples: Sequence[TimelineSample],
    *,
    window_id: str,
    event_id: str,
    participant_id: str,
    target_anchor_ms: int,
    lookback_ms: int,
    guard_ms: int = 0,
    transformation_mode: TransformationMode = TransformationMode.CAUSAL,
) -> PreEventWindow:
    if not samples:
        raise ValueError("预事件窗口不能从空时间轴生成。")
    if lookback_ms <= 0:
        raise ValueError("lookback_ms 必须大于 0。")
    if guard_ms < 0 or guard_ms >= lookback_ms:
        raise ValueError("guard_ms 必须大于等于 0 且小于 lookback_ms。")
    if transformation_mode is not TransformationMode.CAUSAL:
        raise TemporalLeakageError("预事件窗口禁止非因果/双向变换。")
    if any(sample.participant_id != participant_id for sample in samples):
        raise TemporalLeakageError("预事件时间轴不能跨参与者混合。")
    if any(not all(isfinite(value) for value in sample.values) for sample in samples):
        raise ValueError("时间轴数值必须全部为有限数。")

    timestamps = tuple(sample.timestamp_ms for sample in samples)
    if any(right <= left for left, right in zip(timestamps, timestamps[1:])):
        raise TemporalLeakageError("时间轴必须严格递增，禁止乱序或重复。")

    cutoff_ms = target_anchor_ms - guard_ms
    requested_start_ms = target_anchor_ms - lookback_ms
    selected = tuple(
        sample
        for sample in samples
        if requested_start_ms <= sample.timestamp_ms < cutoff_ms
    )
    if not selected:
        raise ValueError("冻结范围内没有可用的严格预事件样本。")

    window = PreEventWindow(
        window_id=window_id,
        event_id=event_id,
        participant_id=participant_id,
        target_anchor_ms=target_anchor_ms,
        requested_start_ms=requested_start_ms,
        cutoff_ms=cutoff_ms,
        transformation_mode=transformation_mode,
        samples=selected,
    )
    leakage = scan_temporal_leakage((window,))
    if leakage:
        raise TemporalLeakageError(leakage[0])
    return window


def scan_temporal_leakage(windows: Iterable[PreEventWindow]) -> tuple[str, ...]:
    findings: list[str] = []
    for window in windows:
        if window.transformation_mode is not TransformationMode.CAUSAL:
            findings.append(f"{window.window_id}: 使用了非因果变换。")
        if any(sample.participant_id != window.participant_id for sample in window.samples):
            findings.append(f"{window.window_id}: 混入其他参与者样本。")
        if any(sample.timestamp_ms >= window.cutoff_ms for sample in window.samples):
            findings.append(f"{window.window_id}: 包含截止点或之后的未来样本。")
        if window.samples and window.source_max_timestamp_ms >= window.target_anchor_ms:
            findings.append(f"{window.window_id}: 包含事件锚点或事件后样本。")
    return tuple(findings)


def participant_overlap(
    training_participants: Iterable[str],
    evaluation_participants: Iterable[str],
) -> tuple[str, ...]:
    return tuple(sorted(set(training_participants) & set(evaluation_participants)))


def assert_participant_disjoint(
    training_participants: Iterable[str],
    evaluation_participants: Iterable[str],
) -> None:
    overlap = participant_overlap(training_participants, evaluation_participants)
    if overlap:
        raise TemporalLeakageError(f"参与者交叉不为 0：{', '.join(overlap)}")
