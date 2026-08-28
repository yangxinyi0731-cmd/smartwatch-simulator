from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.app.contracts import ModelKind, TruthCategory
from backend.app.database import Database, SCHEMA_VERSION, _SCHEMA_V1


SHA256 = "a" * 64


def test_v2_migration_preserves_v1_case_without_inventing_metadata(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "migration.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(_SCHEMA_V1)
        connection.execute(
            "INSERT INTO schema_migrations (version, applied_at) "
            "VALUES (1, '2026-08-28T00:00:00Z')"
        )
        connection.execute(
            "INSERT INTO cases (case_id, title, truth_category, source_dataset, "
            "source_reference, source_sha256, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy-001",
                "结构版本 1 测试案例",
                "REAL_LAB_ACTIVITY",
                "test-dataset",
                "https://example.test/source",
                SHA256,
                "2026-08-28T00:00:00Z",
            ),
        )
        connection.execute(
            "INSERT INTO cases (case_id, title, truth_category, source_dataset, "
            "source_reference, source_sha256, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                "legacy-derived",
                "缺少旧版父关系的派生案例",
                "DERIVED_PERTURBATION",
                "test-derived-dataset",
                "https://example.test/derived-source",
                "b" * 64,
                "2026-08-28T00:00:01Z",
            ),
        )
        connection.execute("PRAGMA user_version = 1")

    Database(database_path).initialize()

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == 4
        migration_versions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        )
        assert migration_versions == (1, 2, 3, 4)

        case = connection.execute(
            "SELECT * FROM cases WHERE case_id = 'legacy-001'"
        ).fetchone()
        assert case is not None
        assert case["source_record_path"] == "legacy-unrecorded"
        assert case["age_group"] == "UNKNOWN"
        assert case["device_name"] == "UNKNOWN"
        assert json.loads(case["allowed_models_json"]) == []

        source = connection.execute(
            "SELECT * FROM data_sources WHERE source_id = ?",
            ("legacy-case-legacy-001",),
        ).fetchone()
        assert source is not None
        assert source["license_status"] == "UNVERIFIED"
        assert source["redistribution_allowed"] is None

        derived = connection.execute(
            "SELECT truth_category, derivation_parent_case_id, source_record_path, "
            "allowed_models_json FROM cases WHERE case_id = 'legacy-derived'"
        ).fetchone()
        assert derived is not None
        assert derived["truth_category"] == "DERIVED_PERTURBATION"
        assert derived["derivation_parent_case_id"] is None
        assert derived["source_record_path"] == "legacy-unrecorded"
        assert json.loads(derived["allowed_models_json"]) == []


def test_v2_creates_all_contract_tables(tmp_path: Path) -> None:
    database_path = tmp_path / "empty.sqlite3"
    Database(database_path).initialize()

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert SCHEMA_VERSION == 4
    assert {
        "schema_migrations",
        "data_sources",
        "cases",
        "sensor_streams",
        "model_manifests",
        "replay_sessions",
        "replay_events",
        "model_outputs",
        "import_runs",
        "case_import_runs",
        "case_source_files",
        "sensor_quality",
        "ground_truth_events",
        "routine_profiles",
        "routine_events",
    } <= tables


def test_case_catalog_supports_server_pagination_and_filters(tmp_path: Path) -> None:
    database = Database(tmp_path / "catalog.sqlite3")
    database.initialize()
    with database.connect() as connection:
        with connection:
            connection.execute(
                "INSERT INTO data_sources (source_id, name, source_url, fixed_version, "
                "license_status, license_reference, redistribution_allowed, verified_at, "
                "notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "source-test",
                    "测试来源",
                    "https://example.test/source",
                    "test-version",
                    "UNVERIFIED",
                    "test-only",
                    None,
                    "2026-08-28T00:00:00Z",
                    "只用于自动测试。",
                ),
            )
            for index, (truth, allowed_models) in enumerate(
                (
                    ("REAL_LAB_ACTIVITY", ["ACTIVITY_RECOGNITION"]),
                    ("SIMULATED_FALL", ["FALL_DETECTION"]),
                    ("SYNTHETIC_ROUTINE", ["ROUTINE_ANOMALY"]),
                ),
                start=1,
            ):
                connection.execute(
                    "INSERT INTO cases (case_id, title, description, truth_category, "
                    "source_id, source_record_path, source_sha256, participant_id, "
                    "age_group, device_name, wear_position, original_sample_rate_hz, "
                    "activity_label, has_accelerometer, has_gyroscope, "
                    "allowed_models_json, derivation_parent_case_id, processing_command, "
                    "created_at, updated_at) VALUES (?, ?, '', ?, ?, ?, ?, NULL, ?, ?, ?, "
                    "?, ?, ?, ?, ?, NULL, ?, ?, ?)",
                    (
                        f"case-{index:03d}",
                        f"合同测试案例 {index}",
                        truth,
                        "source-test",
                        f"records/case-{index:03d}.csv",
                        f"{index:064x}",
                        "NOT_APPLICABLE" if truth == "SYNTHETIC_ROUTINE" else "UNKNOWN",
                        "测试设备",
                        "wrist",
                        None if truth == "SYNTHETIC_ROUTINE" else 50,
                        "walk" if index == 1 else None,
                        0 if truth == "SYNTHETIC_ROUTINE" else 1,
                        1 if truth == "SIMULATED_FALL" else 0,
                        json.dumps(allowed_models),
                        "pytest seed",
                        f"2026-08-28T00:00:0{index}Z",
                        f"2026-08-28T00:00:0{index}Z",
                    ),
                )

    first_page, total = database.list_cases(page=1, page_size=2)
    assert total == 3
    assert len(first_page) == 2

    fall_cases, fall_total = database.list_cases(
        page=1,
        page_size=20,
        truth_category=TruthCategory.SIMULATED_FALL,
        model_kind=ModelKind.FALL_DETECTION,
    )
    assert fall_total == 1
    assert fall_cases[0].case_id == "case-002"

    escaped_query_cases, escaped_query_total = database.list_cases(
        page=1,
        page_size=20,
        query="%",
    )
    assert escaped_query_total == 0
    assert escaped_query_cases == ()
