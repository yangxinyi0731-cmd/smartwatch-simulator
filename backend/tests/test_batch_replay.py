from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.batch_replay import run_batch_replay_task
from backend.app.database import Database
from backend.app.main import create_app
from backend.scripts.sync_runtime_assets import sync


CASE_ID = "synthetic-routine-100-v1"


def _request_hash(case_ids: tuple[str, ...]) -> str:
    return hashlib.sha256(
        json.dumps(list(case_ids), ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def _clone_routine_case(database: Database, case_id: str) -> None:
    with database.connect() as connection:
        connection.execute(
            "INSERT INTO cases ("
            "case_id, title, description, truth_category, source_id, "
            "source_record_path, source_sha256, participant_id, age_group, "
            "device_name, wear_position, original_sample_rate_hz, activity_label, "
            "has_accelerometer, has_gyroscope, allowed_models_json, "
            "derivation_parent_case_id, processing_command, created_at, updated_at"
            ") SELECT ?, title || ' 副本', description, truth_category, source_id, "
            "source_record_path, source_sha256, participant_id, age_group, "
            "device_name, wear_position, original_sample_rate_hz, activity_label, "
            "has_accelerometer, has_gyroscope, allowed_models_json, "
            "derivation_parent_case_id, processing_command, created_at, updated_at "
            "FROM cases WHERE case_id = ?",
            (case_id, CASE_ID),
        )
        connection.commit()


def test_batch_replay_is_idempotent_and_recovers_interrupted_item(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "batch.sqlite3"
    sync(database_path)
    database = Database(database_path)
    case_ids = (CASE_ID,)
    record, created = database.create_batch_replay_task(
        task_id="batch-test-recovery",
        client_request_id="request-recovery-001",
        request_sha256=_request_hash(case_ids),
        case_ids=case_ids,
    )
    assert created is True
    assert record.state == "QUEUED"

    repeated, repeated_created = database.create_batch_replay_task(
        task_id="batch-unused-id",
        client_request_id="request-recovery-001",
        request_sha256=_request_hash(case_ids),
        case_ids=case_ids,
    )
    assert repeated_created is False
    assert repeated.task_id == record.task_id

    with pytest.raises(ValueError, match="不同的批量案例集合"):
        database.create_batch_replay_task(
            task_id="batch-conflict",
            client_request_id="request-recovery-001",
            request_sha256="f" * 64,
            case_ids=case_ids,
        )

    assert database.claim_next_batch_replay_task() == record.task_id
    claimed_item = database.claim_next_batch_replay_item(record.task_id)
    assert claimed_item is not None
    assert claimed_item.state == "RUNNING"
    assert database.recover_interrupted_batch_replays() == 1

    recovered = database.get_batch_replay_task(record.task_id)
    assert recovered is not None
    assert recovered.state == "QUEUED"
    assert recovered.recovery_count == 1
    assert recovered.items[0].state == "PENDING"

    assert database.claim_next_batch_replay_task() == record.task_id
    completed = run_batch_replay_task(database, record.task_id)
    assert completed.state == "COMPLETED"
    assert completed.completed_count == 1
    assert completed.failed_count == 0
    result = completed.items[0].result_summary
    assert result is not None
    assert result["model_kind"] == "ROUTINE_ANOMALY"
    assert result["history_days"] == 100
    assert "医学风险" in str(result["meaning"])


def test_batch_replay_api_runs_persisted_task_and_reuses_request_id(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "batch-api.sqlite3"
    sync(database_path)
    body = {
        "client_request_id": "api-request-0001",
        "case_ids": [CASE_ID],
    }

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.post("/api/batch-replays", json=body)
        assert response.status_code == 202
        task_id = response.json()["task_id"]

        detail = None
        for _ in range(50):
            candidate = client.get(f"/api/batch-replays/{task_id}")
            assert candidate.status_code == 200
            detail = candidate.json()
            if detail["state"] not in {"QUEUED", "RUNNING"}:
                break
            time.sleep(0.02)

        assert detail is not None
        assert detail["state"] == "COMPLETED"
        assert detail["progress"] == 1.0
        assert detail["items"][0]["result_summary"]["model_kind"] == "ROUTINE_ANOMALY"

        repeated = client.post("/api/batch-replays", json=body)
        assert repeated.status_code == 200
        assert repeated.json()["task_id"] == task_id

        listing = client.get("/api/batch-replays?limit=5")
        assert listing.status_code == 200
        assert listing.json()["total"] == 1
        assert listing.json()["items"][0]["task_id"] == task_id


def test_batch_replay_finalizes_with_errors_without_losing_completed_items(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "batch-partial.sqlite3"
    sync(database_path)
    database = Database(database_path)
    second_case_id = "synthetic-routine-copy-partial"
    _clone_routine_case(database, second_case_id)
    case_ids = (CASE_ID, second_case_id)
    record, created = database.create_batch_replay_task(
        task_id="batch-test-partial",
        client_request_id="request-partial-001",
        request_sha256=_request_hash(case_ids),
        case_ids=case_ids,
    )
    assert created is True
    assert database.claim_next_batch_replay_task() == record.task_id

    first = database.claim_next_batch_replay_item(record.task_id)
    assert first is not None
    database.finish_batch_replay_item(
        task_id=record.task_id,
        sequence=first.sequence,
        result_summary={"model_kind": first.model_kind, "meaning": "独立结果"},
    )
    second = database.claim_next_batch_replay_item(record.task_id)
    assert second is not None
    database.finish_batch_replay_item(
        task_id=record.task_id,
        sequence=second.sequence,
        error_message="可公开的回放失败说明。",
    )

    completed = database.finalize_batch_replay_task(record.task_id)
    assert completed.state == "COMPLETED_WITH_ERRORS"
    assert completed.completed_count == 1
    assert completed.failed_count == 1
    assert completed.items[0].result_summary == {
        "model_kind": first.model_kind,
        "meaning": "独立结果",
    }
    assert completed.items[1].error_message == "可公开的回放失败说明。"


def test_failed_batch_replay_marks_all_unfinished_items_terminal(tmp_path: Path) -> None:
    database_path = tmp_path / "batch-failed.sqlite3"
    sync(database_path)
    database = Database(database_path)
    second_case_id = "synthetic-routine-copy-failed"
    _clone_routine_case(database, second_case_id)
    case_ids = (CASE_ID, second_case_id)
    record, _ = database.create_batch_replay_task(
        task_id="batch-test-failed",
        client_request_id="request-failed-001",
        request_sha256=_request_hash(case_ids),
        case_ids=case_ids,
    )
    assert database.claim_next_batch_replay_task() == record.task_id
    assert database.claim_next_batch_replay_item(record.task_id) is not None

    database.fail_batch_replay_task(record.task_id, "批量任务安全终止。")

    failed = database.get_batch_replay_task(record.task_id)
    assert failed is not None
    assert failed.state == "FAILED"
    assert failed.completed_count == 0
    assert failed.failed_count == 2
    assert {item.state for item in failed.items} == {"FAILED"}
    assert all(item.completed_at is not None for item in failed.items)


def test_batch_replay_api_rejects_duplicate_cases_before_creating_task(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "batch-validation.sqlite3"
    sync(database_path)
    with TestClient(create_app(database_path=database_path)) as client:
        response = client.post(
            "/api/batch-replays",
            json={
                "client_request_id": "api-request-duplicate",
                "case_ids": [CASE_ID, CASE_ID],
            },
        )

        assert response.status_code == 422
        listing = client.get("/api/batch-replays")
        assert listing.status_code == 200
        assert listing.json()["total"] == 0
