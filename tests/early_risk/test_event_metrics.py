from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.early_risk.metrics import (
    AlertCandidate,
    Forecast,
    ObservationPeriod,
    TargetEvent,
    evaluate_event_metrics,
    evaluate_suppression_impact,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    PROJECT_ROOT / "tests" / "early_risk" / "fixtures" / "deterministic_timeline.v1.json"
)


def load_fixture() -> tuple[
    tuple[TargetEvent, ...],
    tuple[AlertCandidate, ...],
    tuple[ObservationPeriod, ...],
    tuple[Forecast, ...],
]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return (
        tuple(TargetEvent(**item) for item in payload["events"]),
        tuple(AlertCandidate(**item) for item in payload["alerts"]),
        tuple(ObservationPeriod(**item) for item in payload["observations"]),
        tuple(Forecast(**item) for item in payload["forecasts"]),
    )


def test_gold_fixture_event_metrics_match_registered_formulas() -> None:
    events, alerts, observations, forecasts = load_fixture()
    report = evaluate_event_metrics(
        events=events,
        alerts=alerts,
        observations=observations,
        forecasts=forecasts,
    )

    recalls = {
        row["horizon_seconds"]: row["recall"]
        for row in report["event_recall_by_lead_time"]
    }
    assert recalls == {1: 0.5, 2: 0.5, 3: 0.5, 5: 0.5, 10: 0.0}
    assert report["event_precision"] == pytest.approx(2 / 3)
    assert report["auprc"] == 1.0
    assert report["false_alerts_per_person_day"]["overall_per_person_day"] == 0.5
    assert report["late_and_missed"] == {
        "late_after_instability": 1,
        "missed": 0,
    }
    assert report["lead_time_distribution_seconds"]["negative_count"] == 1
    assert report["coverage_and_abstention"]["coverage"] == pytest.approx(0.925)


def test_suppression_impact_is_reported_before_and_after() -> None:
    events, alerts, observations, forecasts = load_fixture()
    impact = evaluate_suppression_impact(
        events=events,
        alerts=alerts,
        observations=observations,
        forecasts=forecasts,
    )

    assert impact["suppressed_candidate_count"] == 1
    assert impact["before"]["false_alerts_per_person_day"]["false_alert_count"] == 2
    assert impact["after"]["false_alerts_per_person_day"]["false_alert_count"] == 1
    assert impact["false_alert_reduction_count"] == 1


def test_false_alarm_metric_requires_real_observation_denominator() -> None:
    events, alerts, _, forecasts = load_fixture()
    with pytest.raises(ValueError, match="缺少连续观察时长分母"):
        evaluate_event_metrics(
            events=events,
            alerts=alerts,
            observations=(
                ObservationPeriod(
                    participant_id="fixture-p02",
                    observed_ms=86_400_000,
                    evaluable_ms=86_400_000,
                ),
            ),
            forecasts=forecasts,
        )
