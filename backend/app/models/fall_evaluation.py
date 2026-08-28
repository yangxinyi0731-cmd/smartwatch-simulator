from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .fall import FallModelAdapter


WINDOW_SAMPLES = 200
STRIDE_SAMPLES = 50
SAMPLE_RATE_HZ = 50


@dataclass(frozen=True, slots=True)
class AlarmEpisode:
    start_offset_ms: int
    end_offset_ms: int
    peak_probability: float
    window_count: int


def make_windows(data: np.ndarray) -> tuple[np.ndarray, tuple[int, ...]]:
    values = np.asarray(data, dtype=np.float32)
    if values.ndim != 2 or values.shape[1] != 6:
        raise ValueError("案例传感器数组必须是 [samples, 6]。")
    if len(values) < WINDOW_SAMPLES:
        return np.empty((0, WINDOW_SAMPLES, 6), dtype=np.float32), ()
    starts = tuple(range(0, len(values) - WINDOW_SAMPLES + 1, STRIDE_SAMPLES))
    windows = np.stack(
        [values[start : start + WINDOW_SAMPLES] for start in starts],
        axis=0,
    )
    return windows, starts


def merge_alarm_windows(
    starts: Sequence[int],
    probabilities: Sequence[float],
    threshold: float,
) -> tuple[AlarmEpisode, ...]:
    alarms = [
        (
            int(round(start * 1000 / SAMPLE_RATE_HZ)),
            int(round((start + WINDOW_SAMPLES) * 1000 / SAMPLE_RATE_HZ)),
            float(probability),
        )
        for start, probability in zip(starts, probabilities, strict=True)
        if probability >= threshold
    ]
    if not alarms:
        return ()
    episodes: list[AlarmEpisode] = []
    current_start, current_end, current_peak = alarms[0]
    current_count = 1
    for start_ms, end_ms, probability in alarms[1:]:
        if start_ms <= current_end:
            current_end = max(current_end, end_ms)
            current_peak = max(current_peak, probability)
            current_count += 1
        else:
            episodes.append(
                AlarmEpisode(
                    start_offset_ms=current_start,
                    end_offset_ms=current_end,
                    peak_probability=current_peak,
                    window_count=current_count,
                )
            )
            current_start, current_end, current_peak = start_ms, end_ms, probability
            current_count = 1
    episodes.append(
        AlarmEpisode(
            start_offset_ms=current_start,
            end_offset_ms=current_end,
            peak_probability=current_peak,
            window_count=current_count,
        )
    )
    return tuple(episodes)


def infer_case(
    adapter: FallModelAdapter,
    data: np.ndarray,
) -> tuple[np.ndarray, tuple[AlarmEpisode, ...]]:
    windows, starts = make_windows(data)
    if len(windows) == 0:
        return np.empty(0, dtype=np.float32), ()
    probabilities = adapter.predict_fall_probability(windows)
    return probabilities, merge_alarm_windows(starts, probabilities, adapter.threshold)


def overlaps(
    episode: AlarmEpisode,
    start_offset_ms: int,
    end_offset_ms: int,
) -> bool:
    return min(episode.end_offset_ms, end_offset_ms) > max(
        episode.start_offset_ms, start_offset_ms
    )
