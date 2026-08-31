from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.early_risk.policy import PolicyConfig, PolicyInput, run_dry_policy


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    PROJECT_ROOT / "tests" / "early_risk" / "fixtures" / "deterministic_timeline.v1.json"
)


def test_policy_records_dry_run_candidate_without_external_notification() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    config = PolicyConfig(
        threshold_on=0.8,
        threshold_off=0.4,
        consecutive_required=2,
        cooldown_ms=5000,
    )
    decisions = run_dry_policy(
        tuple(PolicyInput(**item) for item in payload["policy_inputs"]), config
    )

    assert sum(item.action == "RECORD_DRY_RUN_CANDIDATE" for item in decisions) == 1
    assert sum(item.action == "SUPPRESSED" for item in decisions) == 1
    assert all(item.external_notification_sent is False for item in decisions)


def test_policy_refuses_non_dry_run_configuration() -> None:
    with pytest.raises(ValueError, match="禁止真实通知"):
        PolicyConfig(
            threshold_on=0.8,
            threshold_off=0.4,
            consecutive_required=2,
            cooldown_ms=5000,
            dry_run=False,
        )


def test_policy_refuses_time_reversal() -> None:
    config = PolicyConfig(
        threshold_on=0.8,
        threshold_off=0.4,
        consecutive_required=2,
        cooldown_ms=5000,
    )
    with pytest.raises(ValueError, match="严格递增"):
        run_dry_policy(
            (
                PolicyInput(timestamp_ms=2000, score=0.9),
                PolicyInput(timestamp_ms=1000, score=0.9),
            ),
            config,
        )
