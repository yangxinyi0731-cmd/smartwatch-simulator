from __future__ import annotations

from pathlib import Path

from research.early_risk.target_contract import (
    contract_completeness,
    load_target_contract,
    target_contract_sha256,
)
from research.early_risk.validate_contract import build_validation_result


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PROJECT_ROOT / "configs" / "early_risk" / "target_contract.v1.yaml"


def test_truth_contract_is_complete_frozen_e0() -> None:
    contract = load_target_contract(CONTRACT_PATH)

    assert contract.status == "FROZEN_ENGINEERING_V1"
    assert contract.evidence_level == "E0"
    assert contract.prediction_evidence is False
    assert contract.immediate_horizons_seconds == (1, 2, 3, 5, 10)
    assert contract.background_horizons_hours == (24, 168)
    assert contract.synchronization_error_limit_ms == 100
    assert contract_completeness(contract) == 1.0
    assert len(target_contract_sha256(contract)) == 64


def test_truth_contract_validation_does_not_invent_formal_signoff() -> None:
    result = build_validation_result(CONTRACT_PATH)

    assert result["required_field_completeness"] == 1.0
    assert result["formal_signoff_complete"] is False
    assert result["prediction_evidence"] is False


def test_event_and_anchor_definitions_are_unique_and_complete() -> None:
    contract = load_target_contract(CONTRACT_PATH)

    event_codes = [event.code for event in contract.target_events]
    anchor_codes = [anchor.code for anchor in contract.time_anchors]
    assert len(event_codes) == len(set(event_codes)) == 8
    assert len(anchor_codes) == len(set(anchor_codes)) == 5
    assert "t_instability" in anchor_codes
    assert "t_alert_perceivable" in anchor_codes
