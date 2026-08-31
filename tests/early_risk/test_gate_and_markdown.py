from __future__ import annotations

from pathlib import Path

from research.early_risk.build_gate_evidence import build_gate_report
from research.early_risk.check_claims import scan_paths
from research.early_risk.verify_markdown import validate_markdown


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_early_risk_markdown_structure_and_whitespace() -> None:
    paths = sorted((PROJECT_ROOT / "docs" / "early_risk").glob("*.md"))
    assert paths
    assert {path.name: validate_markdown(path) for path in paths} == {
        path.name: [] for path in paths
    }


def test_no_assertive_forbidden_claims_in_e0_deliverables() -> None:
    paths = sorted((PROJECT_ROOT / "docs" / "early_risk").glob("*.md"))
    paths += sorted((PROJECT_ROOT / "reports" / "early_risk").rglob("*.json"))
    assert scan_paths(paths) == []


def test_gate_report_passes_engineering_but_does_not_authorize_p3() -> None:
    report = build_gate_report()

    assert report.evidence_level == "E0"
    assert report.prediction_evidence is False
    assert report.results["overall"] == {
        "engineering_status": "PASS_E0_FOUNDATION",
        "next_stage_authorized": False,
        "formal_signoff_complete": False,
    }
    assert report.results["p2"]["temporal_leakage_finding_count"] == 0
    assert report.results["p2"]["external_notification_count"] == 0
