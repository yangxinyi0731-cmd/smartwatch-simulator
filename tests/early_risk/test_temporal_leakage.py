from __future__ import annotations

import pytest

from research.early_risk.temporal import (
    PreEventWindow,
    TemporalLeakageError,
    TimelineSample,
    TransformationMode,
    assert_participant_disjoint,
    scan_temporal_leakage,
    strict_pre_event_window,
)


def timeline() -> tuple[TimelineSample, ...]:
    return tuple(
        TimelineSample("fixture-p01", timestamp_ms, (float(timestamp_ms),))
        for timestamp_ms in (10_000, 12_000, 14_000, 16_000, 18_000, 20_000, 22_000)
    )


def test_strict_truncation_excludes_guard_anchor_and_post_event_samples() -> None:
    window = strict_pre_event_window(
        timeline(),
        window_id="fixture-window-001",
        event_id="fixture-event-001",
        participant_id="fixture-p01",
        target_anchor_ms=20_000,
        lookback_ms=10_000,
        guard_ms=1_000,
    )

    assert [sample.timestamp_ms for sample in window.samples] == [
        10_000,
        12_000,
        14_000,
        16_000,
        18_000,
    ]
    assert scan_temporal_leakage((window,)) == ()


def test_non_causal_transform_and_cross_participant_samples_are_rejected() -> None:
    with pytest.raises(TemporalLeakageError, match="非因果"):
        strict_pre_event_window(
            timeline(),
            window_id="fixture-window-001",
            event_id="fixture-event-001",
            participant_id="fixture-p01",
            target_anchor_ms=20_000,
            lookback_ms=10_000,
            transformation_mode=TransformationMode.NON_CAUSAL,
        )

    mixed = timeline() + (TimelineSample("fixture-p02", 24_000, (1.0,)),)
    with pytest.raises(TemporalLeakageError, match="跨参与者"):
        strict_pre_event_window(
            mixed,
            window_id="fixture-window-001",
            event_id="fixture-event-001",
            participant_id="fixture-p01",
            target_anchor_ms=30_000,
            lookback_ms=25_000,
        )


def test_leakage_scanner_detects_event_anchor_sample() -> None:
    leaky = PreEventWindow(
        window_id="fixture-leaky-window",
        event_id="fixture-event-001",
        participant_id="fixture-p01",
        target_anchor_ms=20_000,
        requested_start_ms=10_000,
        cutoff_ms=20_000,
        transformation_mode=TransformationMode.CAUSAL,
        samples=(TimelineSample("fixture-p01", 20_000, (1.0,)),),
    )

    findings = scan_temporal_leakage((leaky,))
    assert len(findings) == 2


def test_participant_split_overlap_must_be_zero() -> None:
    assert_participant_disjoint(("p01", "p02"), ("p03", "p04"))
    with pytest.raises(TemporalLeakageError, match="p02"):
        assert_participant_disjoint(("p01", "p02"), ("p02", "p03"))
