from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "data" / "catalog" / "self_collected_pending_v1.json"
REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "early_risk"
    / "self_collected_p01_engineering_validation_v1.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_p01_registry_tracks_all_deidentified_cases() -> None:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert registry["status"] == "ENGINEERING_VALIDATED"
    assert registry["received_case_count"] == 30
    assert registry["accepted_case_count"] == 30
    assert registry["rejected_case_count"] == 0
    assert registry["participant_count"] == 1
    assert registry["action_count"] == 6
    assert registry["claim_enabled"] is True
    assert all(registry["cohort_checks"].values())
    assert len(registry["cases"]) == 30
    assert len({case["case_id"] for case in registry["cases"]}) == 30
    assert {case["participant_id"] for case in registry["cases"]} == {"P01"}
    assert registry["source_archive"]["raw_archive_committed"] is False
    assert registry["source_archive"]["metadata_committed"] is False

    for case in registry["cases"]:
        path = PROJECT_ROOT / case["canonical_relative_path"]
        assert path.is_file()
        assert _sha256(path) == case["canonical_sha256"]
        assert case["truth_category"] == "REAL_LAB_ACTIVITY"
        assert case["accepted_for_engineering_validation"] is True
        assert case["duration_s"] >= 20.0
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            assert next(reader) == ["time_s", "ax", "ay", "az", "gx", "gy", "gz"]
            first = next(reader)
            assert first[0] == "0.00"
            assert len(first) == 7


def test_p01_report_keeps_engineering_claim_narrow() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    assert report["scope"]["participant_count"] == 1
    assert report["scope"]["received_case_count"] == 30
    assert report["scope"]["accepted_case_count"] == 30
    assert report["scope"]["rejected_case_count"] == 0
    assert report["scope"]["model_parameters_changed"] is False
    assert report["engineering_results"]["full_three_model_pipeline_case_count"] == 30
    assert all(report["engineering_results"]["cohort_checks"].values())
    assert report["engineering_results"]["fall_candidate_case_count"] == 7
    assert len(report["cases"]) == 30
    assert any("不能证明跨参与者泛化能力" in item for item in report["limitations"])
    assert any("原始压缩包" in item for item in report["limitations"])
