from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from research.early_risk.baselines import baseline_registry
from research.early_risk.common import (
    PROJECT_ROOT,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
    write_json_if_changed,
)
from research.early_risk.metrics import (
    AlertCandidate,
    Forecast,
    ObservationPeriod,
    TargetEvent,
    evaluate_event_metrics,
    evaluate_suppression_impact,
)
from research.early_risk.policy import PolicyConfig, PolicyInput, run_dry_policy
from research.early_risk.reporting import E0Report
from research.early_risk.temporal import (
    TimelineSample,
    scan_temporal_leakage,
    strict_pre_event_window,
)


DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "early_risk" / "baselines.v1.yaml"
DEFAULT_FIXTURE = (
    PROJECT_ROOT
    / "tests"
    / "early_risk"
    / "fixtures"
    / "deterministic_timeline.v1.json"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "early_risk" / "e0" / "fixture_benchmark.json"


def _load_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("基线配置顶层必须是对象。")
    if payload.get("evidence_level") != "E0" or payload.get("prediction_evidence") is not False:
        raise ValueError("P2 基线配置必须固定为 E0 且 prediction_evidence=false。")
    expected = {baseline.baseline_id for baseline in baseline_registry()}
    configured = {item["id"] for item in payload["baselines"]}
    if configured != expected:
        raise ValueError("基线配置与职责受限登记表不一致。")
    if payload["policy_fixture"].get("dry_run") is not True:
        raise ValueError("P2 策略夹具必须保持 dry_run=true。")
    return payload


def build_fixture_report(config_path: Path, fixture_path: Path) -> E0Report:
    config_path = (
        config_path.resolve()
        if config_path.is_absolute()
        else (PROJECT_ROOT / config_path).resolve()
    )
    fixture_path = (
        fixture_path.resolve()
        if fixture_path.is_absolute()
        else (PROJECT_ROOT / fixture_path).resolve()
    )
    config = _load_config(config_path)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("evidence_level") != "E0" or fixture.get("prediction_evidence") is not False:
        raise ValueError("确定性夹具必须固定为 E0 且 prediction_evidence=false。")

    timeline = tuple(
        TimelineSample(
            participant_id=item["participant_id"],
            timestamp_ms=item["timestamp_ms"],
            values=tuple(item["values"]),
        )
        for item in fixture["timeline_samples"]
    )
    pre_event = strict_pre_event_window(
        timeline,
        window_id="fixture-window-e01",
        event_id="fixture-e01",
        participant_id="fixture-p01",
        target_anchor_ms=20_000,
        lookback_ms=10_000,
        guard_ms=1_000,
    )
    leakage_findings = scan_temporal_leakage((pre_event,))

    events = tuple(TargetEvent(**item) for item in fixture["events"])
    alerts = tuple(AlertCandidate(**item) for item in fixture["alerts"])
    observations = tuple(
        ObservationPeriod(**item) for item in fixture["observations"]
    )
    forecasts = tuple(Forecast(**item) for item in fixture["forecasts"])
    matching = config["event_matching"]
    metric_options = {
        "horizons_seconds": tuple(config["horizons_seconds"]),
        "maximum_pre_event_seconds": matching["maximum_pre_event_seconds"],
        "late_grace_seconds": matching["late_grace_seconds"],
        "merge_gap_seconds": matching["duplicate_alert_merge_seconds"],
    }
    metrics = evaluate_event_metrics(
        events=events,
        alerts=alerts,
        observations=observations,
        forecasts=forecasts,
        **metric_options,
    )
    suppression = evaluate_suppression_impact(
        events=events,
        alerts=alerts,
        observations=observations,
        forecasts=forecasts,
        **metric_options,
    )

    policy_config = PolicyConfig(**config["policy_fixture"])
    policy_inputs = tuple(PolicyInput(**item) for item in fixture["policy_inputs"])
    policy_decisions = run_dry_policy(policy_inputs, policy_config)
    if any(decision.external_notification_sent for decision in policy_decisions):
        raise ValueError("E0 dry-run 状态机不得产生真实外部通知。")

    return E0Report(
        report_id="early-risk-fixture-benchmark-v1",
        generated_from=(
            str(config_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            str(fixture_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        ),
        claims=(
            "确定性夹具上的合同、防泄漏、事件级指标和 dry-run 状态机可重复运行。",
            "报告只验证公式与软件行为，不提供真实老人提前预测证据。",
        ),
        limitations=(
            "全部事件、告警、分数和时间线均为人工确定性工程夹具。",
            "夹具指标不得作为真实召回、精确率、AUPRC、校准或误报/人日对外发布。",
            "策略只记录 dry-run 候选，不振动、不发声、不通知家属或救援方。",
        ),
        results={
            "config_sha256": sha256_file(config_path),
            "fixture_sha256": sha256_file(fixture_path),
            "temporal_leakage": {
                "finding_count": len(leakage_findings),
                "findings": list(leakage_findings),
                "selected_timestamp_ms": [
                    sample.timestamp_ms for sample in pre_event.samples
                ],
                "source_max_timestamp_ms": pre_event.source_max_timestamp_ms,
                "target_anchor_ms": pre_event.target_anchor_ms,
                "post_event_samples_in_source_fixture_are_excluded": True,
            },
            "metrics": metrics,
            "suppression_impact": suppression,
            "policy": {
                "dry_run": policy_config.dry_run,
                "decision_count": len(policy_decisions),
                "dry_run_candidate_count": sum(
                    decision.action == "RECORD_DRY_RUN_CANDIDATE"
                    for decision in policy_decisions
                ),
                "external_notification_count": sum(
                    decision.external_notification_sent for decision in policy_decisions
                ),
                "decisions": [
                    {
                        "timestamp_ms": decision.timestamp_ms,
                        "state": decision.state,
                        "evidence_count": decision.evidence_count,
                        "action": decision.action,
                        "reason": decision.reason,
                        "external_notification_sent": decision.external_notification_sent,
                    }
                    for decision in policy_decisions
                ],
            },
            "baseline_registry": [
                {
                    "baseline_id": baseline.baseline_id,
                    "role": baseline.role,
                    "allowed_use": baseline.allowed_use,
                    "prohibited_interpretation": baseline.prohibited_interpretation,
                    "evidence_level": baseline.evidence_level,
                    "prediction_evidence": baseline.prediction_evidence,
                    "deployment_approved": baseline.deployment_approved,
                }
                for baseline in baseline_registry()
            ],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="运行确定性 E0 指标与策略夹具。")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    if args.repeat <= 0:
        raise SystemExit("--repeat 必须大于 0。")
    serialized_runs: list[bytes] = []
    report: E0Report | None = None
    for _ in range(args.repeat):
        report = build_fixture_report(args.config, args.fixture)
        serialized_runs.append(canonical_json_bytes(report.model_dump(mode="json")))
    run_hashes = tuple(sha256_bytes(payload) for payload in serialized_runs)
    if len(set(run_hashes)) != 1:
        raise SystemExit("确定性夹具重复运行输出哈希不一致。")
    assert report is not None
    output_path = (
        args.output.resolve()
        if args.output.is_absolute()
        else (PROJECT_ROOT / args.output).resolve()
    )
    write_json_if_changed(output_path, report.model_dump(mode="json"))
    print(
        json.dumps(
            {
                "output": str(output_path.relative_to(PROJECT_ROOT)),
                "repeat": args.repeat,
                "canonical_report_sha256": run_hashes[0],
                "hashes_identical": len(set(run_hashes)) == 1,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
