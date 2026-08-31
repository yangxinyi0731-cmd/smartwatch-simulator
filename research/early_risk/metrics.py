from __future__ import annotations

from dataclasses import dataclass, replace
from math import sqrt
from statistics import mean, median
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class TargetEvent:
    event_id: str
    participant_id: str
    t_instability_ms: int
    t_impact_ms: int | None = None


@dataclass(frozen=True, slots=True)
class AlertCandidate:
    alert_id: str
    participant_id: str
    perceivable_ms: int
    score: float
    suppressed: bool = False
    suppression_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ObservationPeriod:
    participant_id: str
    observed_ms: int
    evaluable_ms: int


@dataclass(frozen=True, slots=True)
class Forecast:
    forecast_id: str
    participant_id: str
    score: float
    outcome: int


@dataclass(frozen=True, slots=True)
class AlertCluster:
    cluster_id: str
    participant_id: str
    perceivable_ms: int
    score: float
    source_alert_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EventMatch:
    event: TargetEvent
    alert: AlertCluster | None

    @property
    def lead_time_ms(self) -> int | None:
        if self.alert is None:
            return None
        return self.event.t_instability_ms - self.alert.perceivable_ms


def _quantile(values: Sequence[float], probability: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    estimate = successes / total
    denominator = 1 + (z**2 / total)
    center = (estimate + (z**2 / (2 * total))) / denominator
    radius = (
        z
        * sqrt((estimate * (1 - estimate) / total) + (z**2 / (4 * total**2)))
        / denominator
    )
    return (max(0.0, center - radius), min(1.0, center + radius))


def merge_alerts(
    alerts: Iterable[AlertCandidate],
    *,
    merge_gap_ms: int,
) -> tuple[AlertCluster, ...]:
    if merge_gap_ms < 0:
        raise ValueError("merge_gap_ms 不能为负数。")
    ordered = sorted(alerts, key=lambda item: (item.participant_id, item.perceivable_ms))
    clusters: list[AlertCluster] = []
    for alert in ordered:
        if not 0 <= alert.score <= 1:
            raise ValueError("告警分数必须在 0–1。")
        if (
            clusters
            and clusters[-1].participant_id == alert.participant_id
            and alert.perceivable_ms - clusters[-1].perceivable_ms <= merge_gap_ms
        ):
            previous = clusters[-1]
            clusters[-1] = replace(
                previous,
                score=max(previous.score, alert.score),
                source_alert_ids=previous.source_alert_ids + (alert.alert_id,),
            )
        else:
            clusters.append(
                AlertCluster(
                    cluster_id=f"cluster-{alert.alert_id}",
                    participant_id=alert.participant_id,
                    perceivable_ms=alert.perceivable_ms,
                    score=alert.score,
                    source_alert_ids=(alert.alert_id,),
                )
            )
    return tuple(clusters)


def match_events(
    events: Iterable[TargetEvent],
    clusters: Iterable[AlertCluster],
    *,
    maximum_pre_event_ms: int,
    late_grace_ms: int,
) -> tuple[tuple[EventMatch, ...], tuple[AlertCluster, ...]]:
    ordered_events = sorted(events, key=lambda item: (item.participant_id, item.t_instability_ms))
    ordered_clusters = tuple(
        sorted(clusters, key=lambda item: (item.participant_id, item.perceivable_ms))
    )
    used: set[str] = set()
    matches: list[EventMatch] = []
    for event in ordered_events:
        candidates = [
            cluster
            for cluster in ordered_clusters
            if cluster.cluster_id not in used
            and cluster.participant_id == event.participant_id
            and event.t_instability_ms - maximum_pre_event_ms
            <= cluster.perceivable_ms
            <= event.t_instability_ms + late_grace_ms
        ]
        # The first perceivable alert is the lead-time anchor; later duplicates do not
        # manufacture a different lead time.
        selected = min(candidates, key=lambda item: item.perceivable_ms, default=None)
        if selected is not None:
            used.add(selected.cluster_id)
        matches.append(EventMatch(event=event, alert=selected))
    unmatched = tuple(cluster for cluster in ordered_clusters if cluster.cluster_id not in used)
    return tuple(matches), unmatched


def average_precision(forecasts: Sequence[Forecast]) -> float | None:
    positives = sum(forecast.outcome for forecast in forecasts)
    if not forecasts or positives == 0:
        return None
    ordered = sorted(forecasts, key=lambda item: (-item.score, item.forecast_id))
    true_positives = 0
    precision_sum = 0.0
    for rank, forecast in enumerate(ordered, start=1):
        if forecast.outcome not in (0, 1) or not 0 <= forecast.score <= 1:
            raise ValueError("Forecast 必须使用 0/1 结果和 0–1 分数。")
        if forecast.outcome == 1:
            true_positives += 1
            precision_sum += true_positives / rank
    return precision_sum / positives


def calibration_metrics(
    forecasts: Sequence[Forecast], *, bins: int = 10
) -> dict[str, float | int | None]:
    if not forecasts:
        return {"count": 0, "brier": None, "ece": None}
    if bins <= 0:
        raise ValueError("bins 必须大于 0。")
    for forecast in forecasts:
        if forecast.outcome not in (0, 1) or not 0 <= forecast.score <= 1:
            raise ValueError("Forecast 必须使用 0/1 结果和 0–1 分数。")
    brier = mean((forecast.score - forecast.outcome) ** 2 for forecast in forecasts)
    ece = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        members = [
            forecast
            for forecast in forecasts
            if lower <= forecast.score < upper
            or (index == bins - 1 and forecast.score == 1)
        ]
        if not members:
            continue
        confidence = mean(item.score for item in members)
        observed = mean(item.outcome for item in members)
        ece += (len(members) / len(forecasts)) * abs(confidence - observed)
    return {"count": len(forecasts), "brier": brier, "ece": ece}


def _false_alarm_burden(
    unmatched: Sequence[AlertCluster], observations: Sequence[ObservationPeriod]
) -> dict[str, object]:
    days_by_participant = {
        observation.participant_id: observation.observed_ms / 86_400_000
        for observation in observations
    }
    if any(days <= 0 for days in days_by_participant.values()):
        raise ValueError("每个参与者的观察时长必须大于 0。")
    counts = {participant: 0 for participant in days_by_participant}
    for alert in unmatched:
        if alert.participant_id not in counts:
            raise ValueError("告警参与者缺少连续观察时长分母。")
        counts[alert.participant_id] += 1
    rates = [counts[participant] / days for participant, days in days_by_participant.items()]
    total_days = sum(days_by_participant.values())
    return {
        "false_alert_count": len(unmatched),
        "person_days": total_days,
        "overall_per_person_day": len(unmatched) / total_days,
        "mean": mean(rates) if rates else None,
        "median": median(rates) if rates else None,
        "p95": _quantile(rates, 0.95),
        "maximum": max(rates, default=None),
        "by_participant": dict(sorted(zip(days_by_participant, rates))),
    }


def evaluate_event_metrics(
    *,
    events: Sequence[TargetEvent],
    alerts: Sequence[AlertCandidate],
    observations: Sequence[ObservationPeriod],
    forecasts: Sequence[Forecast],
    horizons_seconds: Sequence[int] = (1, 2, 3, 5, 10),
    maximum_pre_event_seconds: int = 10,
    late_grace_seconds: int = 2,
    merge_gap_seconds: int = 3,
) -> dict[str, object]:
    active_alerts = tuple(alert for alert in alerts if not alert.suppressed)
    clusters = merge_alerts(active_alerts, merge_gap_ms=merge_gap_seconds * 1000)
    matches, unmatched = match_events(
        events,
        clusters,
        maximum_pre_event_ms=maximum_pre_event_seconds * 1000,
        late_grace_ms=late_grace_seconds * 1000,
    )
    lead_times = [match.lead_time_ms / 1000 for match in matches if match.lead_time_ms is not None]
    matched_count = len(lead_times)
    event_count = len(events)
    recall_by_horizon: list[dict[str, object]] = []
    for horizon in horizons_seconds:
        timely = sum(lead >= horizon for lead in lead_times)
        lower, upper = wilson_interval(timely, event_count)
        recall_by_horizon.append(
            {
                "horizon_seconds": horizon,
                "timely_event_count": timely,
                "event_count": event_count,
                "recall": timely / event_count if event_count else None,
                "ci95_wilson": [lower, upper] if event_count else None,
            }
        )

    total_observed = sum(item.observed_ms for item in observations)
    total_evaluable = sum(item.evaluable_ms for item in observations)
    if total_observed <= 0 or any(item.evaluable_ms > item.observed_ms for item in observations):
        raise ValueError("覆盖率分母必须有效，且可评估时长不能超过观察时长。")

    ap = average_precision(forecasts)
    prevalence = (
        sum(item.outcome for item in forecasts) / len(forecasts) if forecasts else None
    )
    false_alarm_burden = _false_alarm_burden(unmatched, observations)
    matched_clusters = matched_count
    return {
        "event_recall_by_lead_time": recall_by_horizon,
        "event_precision": (
            matched_clusters / len(clusters) if clusters else None
        ),
        "matched_event_count": matched_count,
        "event_count": event_count,
        "alert_cluster_count": len(clusters),
        "auprc": ap,
        "no_skill_prevalence": prevalence,
        "false_alerts_per_person_day": false_alarm_burden,
        "calibration": calibration_metrics(forecasts),
        "lead_time_distribution_seconds": {
            "median": median(lead_times) if lead_times else None,
            "q1": _quantile(lead_times, 0.25),
            "q3": _quantile(lead_times, 0.75),
            "minimum": min(lead_times, default=None),
            "maximum": max(lead_times, default=None),
            "negative_count": sum(value < 0 for value in lead_times),
            "zero_count": sum(value == 0 for value in lead_times),
        },
        "coverage_and_abstention": {
            "observed_ms": total_observed,
            "evaluable_ms": total_evaluable,
            "coverage": total_evaluable / total_observed,
            "abstention": 1 - (total_evaluable / total_observed),
        },
        "late_and_missed": {
            "late_after_instability": sum(value < 0 for value in lead_times),
            "missed": sum(match.alert is None for match in matches),
        },
    }


def evaluate_suppression_impact(
    *,
    events: Sequence[TargetEvent],
    alerts: Sequence[AlertCandidate],
    observations: Sequence[ObservationPeriod],
    forecasts: Sequence[Forecast],
    **metric_options: object,
) -> dict[str, object]:
    before_alerts = tuple(replace(alert, suppressed=False) for alert in alerts)
    before = evaluate_event_metrics(
        events=events,
        alerts=before_alerts,
        observations=observations,
        forecasts=forecasts,
        **metric_options,
    )
    after = evaluate_event_metrics(
        events=events,
        alerts=alerts,
        observations=observations,
        forecasts=forecasts,
        **metric_options,
    )
    before_false = before["false_alerts_per_person_day"]["false_alert_count"]
    after_false = after["false_alerts_per_person_day"]["false_alert_count"]
    return {
        "before": before,
        "after": after,
        "suppressed_candidate_count": sum(alert.suppressed for alert in alerts),
        "false_alert_reduction_count": before_false - after_false,
    }
