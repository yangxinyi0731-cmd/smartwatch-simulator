from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.app.contracts import RoutineEventContract
from backend.app.models.routine import RoutineModelAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVENTS_PATH = PROJECT_ROOT / "data" / "cases" / "synthetic_routine_100_v1.json"
MANIFEST_PATH = PROJECT_ROOT / "models" / "routine_anomaly" / "statistical_v1" / "manifest.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "models" / "routine_anomaly_scenarios.json"


def test_committed_routine_history_is_100_days_and_explicitly_synthetic() -> None:
    payload = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    events = tuple(RoutineEventContract.model_validate(item) for item in payload["events"])
    assert payload["history_days"] == 100
    assert payload["event_count"] == len(events)
    assert len({event.started_at.date() for event in events}) == 100
    assert all(event.truth_category.value == "SYNTHETIC_ROUTINE" for event in events)


def test_committed_routine_manifest_and_rules_hash_match() -> None:
    adapter = RoutineModelAdapter(project_root=PROJECT_ROOT, manifest_path=MANIFEST_PATH)
    assert adapter.manifest.deployment_approved is False
    assert adapter.artifact.history_days == 100
    assert adapter.artifact.seed == 20260828


def test_committed_routine_scenario_report_has_no_real_world_metric_claim() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    assert report["scenario_count"] == 5
    assert report["passed_scenario_count"] == 5
    assert all(item["passed"] for item in report["scenarios"])
    assert "不是从真实老人数据计算" in report["meaning"]
    assert report["history"]["events_sha256"] == hashlib.sha256(EVENTS_PATH.read_bytes()).hexdigest()
