from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from research.early_risk.audit_current_data import build_current_data_audit
from research.early_risk.audit_runtime_state import read_runtime_state
from research.early_risk.common import canonical_json_bytes, sha256_bytes
from research.early_risk.export_contracts import OUTPUT_PATH, build_schema
from research.early_risk.run_fixture_benchmark import (
    DEFAULT_CONFIG,
    DEFAULT_FIXTURE,
    build_fixture_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_current_data_audit_covers_all_registered_assets_without_prediction_claim() -> None:
    report = build_current_data_audit()

    assert report.evidence_level == "E0"
    assert report.prediction_evidence is False
    assert report.results["no_download_performed"] is True
    assert report.results["asset_coverage"] == 1.0
    assert report.results["audited_asset_count"] == 11
    assert all(
        model["deployment_approved"] is False
        for model in report.results["model_registry"]
    )


def test_fixture_report_is_byte_deterministic() -> None:
    first = build_fixture_report(DEFAULT_CONFIG, DEFAULT_FIXTURE)
    second = build_fixture_report(DEFAULT_CONFIG, DEFAULT_FIXTURE)

    first_bytes = canonical_json_bytes(first.model_dump(mode="json"))
    second_bytes = canonical_json_bytes(second.model_dump(mode="json"))
    assert first_bytes == second_bytes
    assert sha256_bytes(first_bytes) == sha256_bytes(second_bytes)
    assert first.results["temporal_leakage"]["finding_count"] == 0
    assert first.results["policy"]["external_notification_count"] == 0


def test_committed_early_risk_schema_matches_contract_code() -> None:
    committed = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    assert committed == build_schema()


def test_runtime_state_audit_uses_existing_database_read_only(tmp_path: Path) -> None:
    database_path = tmp_path / "runtime.sqlite3"
    connection = sqlite3.connect(database_path)
    try:
        connection.executescript(
            """
            PRAGMA user_version = 5;
            CREATE TABLE cases (case_id TEXT PRIMARY KEY);
            CREATE TABLE model_manifests (manifest_id TEXT PRIMARY KEY);
            CREATE TABLE batch_replay_tasks (task_id TEXT PRIMARY KEY, state TEXT);
            INSERT INTO cases VALUES ('case-1');
            INSERT INTO model_manifests VALUES ('model-1');
            INSERT INTO batch_replay_tasks VALUES ('task-1', 'COMPLETED');
            """
        )
        connection.commit()
    finally:
        connection.close()

    result = read_runtime_state(database_path)

    assert result["open_mode"] == "read_only"
    assert result["immutable"] is True
    assert result["integrity"] == "ok"
    assert result["schema_version"] == 5
    assert result["cases"] == 1
    assert result["models"] == 1
    assert result["completed_batch_tasks"] == 1
