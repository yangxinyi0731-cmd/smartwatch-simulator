from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.database import SCHEMA_VERSION
from backend.app.database import Database
from backend.app.main import create_app
from backend.app.contracts import ModelManifest
from backend.scripts.sync_runtime_assets import sync


def test_health_initializes_empty_database(tmp_path: Path) -> None:
    database_path = tmp_path / "health-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["event"] == "system.status"
    assert payload["service"]["state"] == "ready"
    assert payload["database"] == {
        "engine": "sqlite",
        "state": "ready",
        "schema_version": SCHEMA_VERSION,
    }
    assert payload["cases"] == {"count": 0, "state": "empty"}
    assert payload["realtime"] == {
        "transport": "websocket",
        "path": "/ws/system",
    }
    assert database_path.is_file()

    with sqlite3.connect(database_path) as connection:
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == SCHEMA_VERSION
        assert int(connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0]) == 0


def test_websocket_publishes_current_system_status(tmp_path: Path) -> None:
    database_path = tmp_path / "websocket-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        with client.websocket_connect("/ws/system") as websocket:
            payload = websocket.receive_json()

    assert payload["event"] == "system.status"
    assert payload["service"]["state"] == "ready"
    assert payload["database"]["state"] == "ready"
    assert payload["cases"]["count"] == 0


def test_contract_catalog_exposes_truth_and_three_model_contracts(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "contracts-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/contracts")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["contract_version"] == "1.0.0"
    assert payload["database_schema_version"] == SCHEMA_VERSION
    assert payload["truth_categories"] == [
        "REAL_FREE_LIVING",
        "REAL_LAB_ACTIVITY",
        "SIMULATED_FALL",
        "SYNTHETIC_ROUTINE",
        "DERIVED_PERTURBATION",
    ]
    assert [item["model_kind"] for item in payload["model_contracts"]] == [
        "FALL_DETECTION",
        "ROUTINE_ANOMALY",
        "ACTIVITY_RECOGNITION",
    ]
    assert all("综合医学风险" not in item for item in payload["model_contracts"])


def test_empty_case_catalog_uses_server_pagination_contract(tmp_path: Path) -> None:
    database_path = tmp_path / "cases-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/cases?page=9&page_size=20")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_pages": 0,
    }


def test_case_catalog_validates_filter_values(tmp_path: Path) -> None:
    database_path = tmp_path / "case-filter-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/cases?truth_category=REAL_ELDERLY_FALL")

    assert response.status_code == 422
    assert "REAL_ELDERLY_FALL" in response.text


def test_model_catalog_returns_registered_research_manifest(tmp_path: Path) -> None:
    database_path = tmp_path / "models-test.sqlite3"
    project_root = Path(__file__).resolve().parents[2]
    manifest = ModelManifest.model_validate_json(
        (project_root / "models/fall_detector/tcn_final_candidate/manifest.json")
        .read_text(encoding="utf-8")
    )

    with TestClient(create_app(database_path=database_path)) as client:
        Database(database_path).register_model_manifest(manifest)
        response = client.get("/api/models")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["manifest_id"] == manifest.manifest_id
    assert item["model_kind"] == "FALL_DETECTION"
    assert item["artifact_sha256"] == manifest.artifact_sha256
    assert item["deployment_approved"] is False
    assert item["approval_status"] == "EXTERNAL_VALIDATION_REQUIRED"
    assert item["external_validation_completed"] is False


def test_report_catalog_normalizes_saved_evidence_without_overclaiming(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "reports-test.sqlite3"
    sync(database_path)

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/reports")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["total"] == 3
    by_kind = {item["model_kind"]: item for item in payload["items"]}
    fall = by_kind["FALL_DETECTION"]
    assert fall["evidence_scope"] == "same_source_behavior_replay"
    assert fall["deployment_approved"] is False
    assert len(fall["report_sha256"]) == 64
    assert {
        metric["key"]: metric["display_value"] for metric in fall["metrics"]
    }["simulated_fall_alert_overlap"] == "40 / 40"
    assert "不是实际老人跌倒" in fall["evidence_scope_note"]
    routine = by_kind["ROUTINE_ANOMALY"]
    assert routine["evidence_scope"] == "deterministic_rule_scenarios"
    assert {
        metric["key"]: metric["display_value"] for metric in routine["metrics"]
    }["rule_scenarios_passed"] == "5 / 5 通过"
    activity = by_kind["ACTIVITY_RECOGNITION"]
    assert activity["evidence_scope"] == "same_dataset_participant_holdout"
    activity_metrics = {
        metric["key"]: metric["display_value"] for metric in activity["metrics"]
    }
    assert activity_metrics["evaluation_windows"] == "3728 个"
    assert activity_metrics["participant_holdout_accuracy"] == "60.8%"
    assert activity_metrics["participant_holdout_macro_f1"] == "0.598"
    assert "不是完整 151 人" in activity["evidence_scope_note"]
    assert all(item["external_validation_completed"] is False for item in payload["items"])
    assert any("不合并" in item for item in payload["disclaimers"])


def test_report_export_is_a_downloadable_json_snapshot(tmp_path: Path) -> None:
    database_path = tmp_path / "report-export-test.sqlite3"
    sync(database_path)

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/reports/export.json")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == (
        'attachment; filename="smartwatch-model-evaluation-reports.json"'
    )
    assert response.json()["total"] == 3


def test_routine_replay_preview_uses_registered_synthetic_events(tmp_path: Path) -> None:
    database_path = tmp_path / "routine-preview.sqlite3"
    sync(database_path)

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get(
            "/api/cases/synthetic-routine-100-v1/replay-preview"
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["case"]["truth_category"] == "SYNTHETIC_ROUTINE"
    assert payload["sensor_stream"] is None
    assert payload["sensor_samples"] == []
    assert payload["fall_windows"] == []
    assert payload["routine_profile"]["history_days"] == 100
    assert payload["routine_profile"]["event_count"] == 551
    assert len(payload["routine_days"]) == 100
    assert all(len(day["assessments"]) == 3 for day in payload["routine_days"])
    assert any("固定种子合成" in message for message in payload["messages"])


def test_replay_preview_returns_sanitized_not_found(tmp_path: Path) -> None:
    database_path = tmp_path / "missing-preview.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/cases/missing/replay-preview")

    assert response.status_code == 404
    assert response.json() == {
        "code": "CASE_NOT_FOUND",
        "message": "没有找到这个测试案例。",
        "retryable": False,
    }


def test_health_reports_sanitized_degraded_state(tmp_path: Path) -> None:
    database_path = tmp_path / "degraded.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        with sqlite3.connect(database_path) as connection:
            connection.execute("DROP TABLE cases")

        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["service"]["state"] == "degraded"
    assert payload["database"] == {
        "engine": "sqlite",
        "state": "unavailable",
        "schema_version": None,
    }
    assert payload["cases"] == {"count": None, "state": "unavailable"}
    assert "SQLite 数据库暂不可用" in payload["message"]
    assert "no such table" not in response.text


def test_case_catalog_reports_sanitized_retryable_failure(tmp_path: Path) -> None:
    database_path = tmp_path / "case-catalog-degraded.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        with sqlite3.connect(database_path) as connection:
            connection.execute("DROP TABLE cases")

        response = client.get("/api/cases")

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "code": "CASE_CATALOG_UNAVAILABLE",
        "message": "案例库暂不可用，请稍后重试。",
        "retryable": True,
    }
    assert "no such table" not in response.text


def test_startup_rejects_newer_database_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "future.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")

    try:
        with TestClient(create_app(database_path=database_path)):
            pass
    except RuntimeError as error:
        assert "拒绝自动降级" in str(error)
    else:
        raise AssertionError("应用不应接受高于当前程序支持版本的数据库。")


def test_built_frontend_can_be_served_by_same_local_process(tmp_path: Path) -> None:
    database_path = tmp_path / "frontend.sqlite3"
    frontend_dist_path = tmp_path / "frontend-dist"
    frontend_dist_path.mkdir()
    (frontend_dist_path / "index.html").write_text(
        "<!doctype html><html><body>本地交付前端</body></html>",
        encoding="utf-8",
    )

    with TestClient(
        create_app(
            database_path=database_path,
            frontend_dist_path=frontend_dist_path,
        )
    ) as client:
        frontend = client.get("/")
        health = client.get("/api/health")

    assert frontend.status_code == 200
    assert "本地交付前端" in frontend.text
    assert health.status_code == 200
