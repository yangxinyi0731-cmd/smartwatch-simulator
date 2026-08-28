from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .contracts import ModelKind, TruthCategory


SCHEMA_VERSION = 2

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    truth_category TEXT NOT NULL CHECK (
        truth_category IN (
            'REAL_FREE_LIVING',
            'REAL_LAB_ACTIVITY',
            'SIMULATED_FALL',
            'SYNTHETIC_ROUTINE',
            'DERIVED_PERTURBATION'
        )
    ),
    source_dataset TEXT NOT NULL CHECK (length(trim(source_dataset)) > 0),
    source_reference TEXT NOT NULL CHECK (length(trim(source_reference)) > 0),
    source_sha256 TEXT NOT NULL CHECK (length(source_sha256) = 64),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cases_truth_category
ON cases (truth_category);
"""

_SCHEMA_V2 = """
ALTER TABLE cases RENAME TO cases_v1_backup;

CREATE TABLE data_sources (
    source_id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    source_url TEXT NOT NULL CHECK (length(trim(source_url)) > 0),
    fixed_version TEXT NOT NULL CHECK (length(trim(fixed_version)) > 0),
    license_status TEXT NOT NULL CHECK (
        license_status IN (
            'VERIFIED_OPEN',
            'LOCAL_RESEARCH_ONLY',
            'APPLICATION_REQUIRED',
            'UNVERIFIED'
        )
    ),
    license_reference TEXT NOT NULL CHECK (length(trim(license_reference)) > 0),
    redistribution_allowed INTEGER CHECK (
        redistribution_allowed IS NULL OR redistribution_allowed IN (0, 1)
    ),
    verified_at TEXT NOT NULL,
    notes TEXT NOT NULL CHECK (length(trim(notes)) > 0)
);

INSERT OR IGNORE INTO data_sources (
    source_id,
    name,
    source_url,
    fixed_version,
    license_status,
    license_reference,
    redistribution_allowed,
    verified_at,
    notes
)
SELECT
    'legacy-case-' || case_id,
    source_dataset,
    source_reference,
    'unrecorded-v1',
    'UNVERIFIED',
    source_reference,
    NULL,
    created_at,
    '由结构版本 1 迁移；正式使用前必须补齐许可与版本核验。'
FROM cases_v1_backup
;

CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description TEXT NOT NULL DEFAULT '',
    truth_category TEXT NOT NULL CHECK (
        truth_category IN (
            'REAL_FREE_LIVING',
            'REAL_LAB_ACTIVITY',
            'SIMULATED_FALL',
            'SYNTHETIC_ROUTINE',
            'DERIVED_PERTURBATION'
        )
    ),
    source_id TEXT NOT NULL REFERENCES data_sources(source_id) ON UPDATE CASCADE,
    source_record_path TEXT NOT NULL CHECK (length(trim(source_record_path)) > 0),
    source_sha256 TEXT NOT NULL CHECK (
        length(source_sha256) = 64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    participant_id TEXT,
    age_group TEXT NOT NULL CHECK (
        age_group IN (
            'YOUNG_ADULT',
            'OLDER_ADULT',
            'MIXED',
            'UNKNOWN',
            'NOT_APPLICABLE'
        )
    ),
    device_name TEXT NOT NULL CHECK (length(trim(device_name)) > 0),
    wear_position TEXT NOT NULL CHECK (length(trim(wear_position)) > 0),
    original_sample_rate_hz REAL CHECK (
        original_sample_rate_hz IS NULL OR original_sample_rate_hz > 0
    ),
    activity_label TEXT,
    has_accelerometer INTEGER NOT NULL CHECK (has_accelerometer IN (0, 1)),
    has_gyroscope INTEGER NOT NULL CHECK (has_gyroscope IN (0, 1)),
    allowed_models_json TEXT NOT NULL CHECK (
        json_valid(allowed_models_json) AND json_type(allowed_models_json) = 'array'
    ),
    derivation_parent_case_id TEXT REFERENCES cases(case_id),
    processing_command TEXT NOT NULL CHECK (length(trim(processing_command)) > 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (
        (truth_category = 'DERIVED_PERTURBATION' AND derivation_parent_case_id IS NOT NULL)
        OR
        (truth_category <> 'DERIVED_PERTURBATION' AND derivation_parent_case_id IS NULL)
        OR
        (
            truth_category = 'DERIVED_PERTURBATION'
            AND derivation_parent_case_id IS NULL
            AND source_record_path = 'legacy-unrecorded'
            AND allowed_models_json = '[]'
        )
    )
);

INSERT INTO cases (
    case_id,
    title,
    description,
    truth_category,
    source_id,
    source_record_path,
    source_sha256,
    participant_id,
    age_group,
    device_name,
    wear_position,
    original_sample_rate_hz,
    activity_label,
    has_accelerometer,
    has_gyroscope,
    allowed_models_json,
    derivation_parent_case_id,
    processing_command,
    created_at,
    updated_at
)
SELECT
    case_id,
    title,
    '',
    truth_category,
    'legacy-case-' || case_id,
    'legacy-unrecorded',
    source_sha256,
    NULL,
    'UNKNOWN',
    'UNKNOWN',
    'UNKNOWN',
    NULL,
    NULL,
    0,
    0,
    '[]',
    NULL,
    'v1-migration: processing command unavailable',
    created_at,
    created_at
FROM cases_v1_backup;

DROP TABLE cases_v1_backup;

CREATE INDEX idx_cases_truth_category ON cases (truth_category);
CREATE INDEX idx_cases_source_id ON cases (source_id);
CREATE INDEX idx_cases_created_at ON cases (created_at DESC, case_id);

CREATE TABLE sensor_streams (
    stream_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
    sensor_kind TEXT NOT NULL CHECK (
        sensor_kind IN ('ACCELEROMETER', 'GYROSCOPE', 'IMU_6AXIS')
    ),
    sample_rate_hz REAL NOT NULL CHECK (sample_rate_hz > 0),
    channels_json TEXT NOT NULL CHECK (
        json_valid(channels_json) AND json_type(channels_json) = 'array'
    ),
    units_json TEXT NOT NULL CHECK (
        json_valid(units_json) AND json_type(units_json) = 'array'
    ),
    sample_count INTEGER NOT NULL CHECK (sample_count > 0),
    duration_ms INTEGER NOT NULL CHECK (duration_ms > 0),
    storage_format TEXT NOT NULL CHECK (storage_format IN ('CSV', 'NPY', 'NPZ')),
    relative_path TEXT NOT NULL CHECK (
        length(trim(relative_path)) > 0
        AND substr(relative_path, 1, 1) NOT IN ('/', char(92))
        AND instr(relative_path, ':') = 0
        AND relative_path NOT LIKE '%..%'
    ),
    content_sha256 TEXT NOT NULL CHECK (
        length(content_sha256) = 64 AND content_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL,
    UNIQUE (case_id, sensor_kind, relative_path)
);

CREATE INDEX idx_sensor_streams_case_id ON sensor_streams (case_id);

CREATE TABLE model_manifests (
    manifest_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_kind TEXT NOT NULL CHECK (
        model_kind IN ('FALL_DETECTION', 'ROUTINE_ANOMALY', 'ACTIVITY_RECOGNITION')
    ),
    version TEXT NOT NULL CHECK (length(trim(version)) > 0),
    format TEXT NOT NULL CHECK (format IN ('ONNX', 'STATISTICAL_RULES')),
    source_commit TEXT NOT NULL CHECK (
        length(source_commit) IN (40, 64)
        AND source_commit NOT GLOB '*[^0-9a-f]*'
    ),
    artifact_relative_path TEXT,
    artifact_sha256 TEXT CHECK (
        artifact_sha256 IS NULL
        OR (
            length(artifact_sha256) = 64
            AND artifact_sha256 NOT GLOB '*[^0-9a-f]*'
        )
    ),
    contract_json TEXT NOT NULL CHECK (json_valid(contract_json)),
    training_provenance_json TEXT NOT NULL CHECK (json_valid(training_provenance_json)),
    evaluation_json TEXT NOT NULL CHECK (json_valid(evaluation_json)),
    limitations_json TEXT NOT NULL CHECK (
        json_valid(limitations_json) AND json_type(limitations_json) = 'array'
    ),
    deployment_approved INTEGER NOT NULL CHECK (deployment_approved IN (0, 1)),
    approval_status TEXT NOT NULL CHECK (
        approval_status IN ('RESEARCH_ONLY', 'EXTERNAL_VALIDATION_REQUIRED', 'APPROVED')
    ),
    external_validation_completed INTEGER NOT NULL CHECK (
        external_validation_completed IN (0, 1)
    ),
    created_at TEXT NOT NULL,
    UNIQUE (model_id, version),
    CHECK (
        (artifact_relative_path IS NULL AND artifact_sha256 IS NULL)
        OR
        (
            artifact_relative_path IS NOT NULL
            AND artifact_sha256 IS NOT NULL
            AND substr(artifact_relative_path, 1, 1) NOT IN ('/', char(92))
            AND instr(artifact_relative_path, ':') = 0
            AND artifact_relative_path NOT LIKE '%..%'
        )
    ),
    CHECK (
        deployment_approved = 0
        OR (
            approval_status = 'APPROVED'
            AND external_validation_completed = 1
        )
    )
);

CREATE INDEX idx_model_manifests_kind ON model_manifests (model_kind);

CREATE TABLE replay_sessions (
    session_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
    client_request_id TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL CHECK (
        state IN ('CREATED', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'RESET')
    ),
    speed REAL NOT NULL CHECK (speed > 0 AND speed <= 16),
    cursor_ms INTEGER NOT NULL CHECK (cursor_ms >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE INDEX idx_replay_sessions_case_id ON replay_sessions (case_id, created_at DESC);

CREATE TABLE replay_events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES replay_sessions(session_id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL CHECK (sequence >= 0),
    event_type TEXT NOT NULL CHECK (
        event_type IN (
            'replay.state_changed',
            'sensor.window',
            'model.output',
            'alert.candidate',
            'replay.error'
        )
    ),
    offset_ms INTEGER NOT NULL CHECK (offset_ms >= 0),
    emitted_at TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK (json_valid(payload_json)),
    UNIQUE (session_id, sequence)
);

CREATE INDEX idx_replay_events_session_sequence
ON replay_events (session_id, sequence);

CREATE TABLE model_outputs (
    output_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES replay_sessions(session_id) ON DELETE CASCADE,
    case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
    manifest_id TEXT NOT NULL REFERENCES model_manifests(manifest_id) ON DELETE RESTRICT,
    model_kind TEXT NOT NULL CHECK (
        model_kind IN ('FALL_DETECTION', 'ROUTINE_ANOMALY', 'ACTIVITY_RECOGNITION')
    ),
    input_window_id TEXT NOT NULL,
    start_offset_ms INTEGER NOT NULL CHECK (start_offset_ms >= 0),
    end_offset_ms INTEGER NOT NULL CHECK (end_offset_ms > start_offset_ms),
    output_json TEXT NOT NULL CHECK (json_valid(output_json)),
    created_at TEXT NOT NULL
);

CREATE INDEX idx_model_outputs_session_time
ON model_outputs (session_id, start_offset_ms, model_kind);
"""


@dataclass(frozen=True, slots=True)
class DatabaseSnapshot:
    schema_version: int
    case_count: int


@dataclass(frozen=True, slots=True)
class CaseListRecord:
    case_id: str
    title: str
    truth_category: str
    source_name: str
    fixed_version: str
    age_group: str
    activity_label: str | None
    allowed_models: tuple[str, ...]
    sensor_stream_count: int
    created_at: str


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path.resolve()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA busy_timeout = 5000")
            yield connection
        finally:
            connection.close()

    def _apply_migration(
        self,
        connection: sqlite3.Connection,
        *,
        version: int,
        script: str,
    ) -> None:
        migration_script = f"""
BEGIN IMMEDIATE;
{script}
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ({version}, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));
PRAGMA user_version = {version};
COMMIT;
"""
        try:
            connection.executescript(migration_script)
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])

            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    "数据库结构版本高于当前程序支持的版本，已拒绝自动降级。"
                )

            if current_version < 1:
                self._apply_migration(connection, version=1, script=_SCHEMA_V1)
                current_version = 1

            if current_version < 2:
                self._apply_migration(connection, version=2, script=_SCHEMA_V2)

    def snapshot(self) -> DatabaseSnapshot:
        with self.connect() as connection:
            connection.execute("SELECT 1").fetchone()
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            case_count = int(connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0])

        if schema_version != SCHEMA_VERSION:
            raise RuntimeError("数据库结构版本与当前程序不一致。")

        return DatabaseSnapshot(schema_version=schema_version, case_count=case_count)

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def list_cases(
        self,
        *,
        page: int,
        page_size: int,
        query: str | None = None,
        truth_category: TruthCategory | None = None,
        model_kind: ModelKind | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[tuple[CaseListRecord, ...], int]:
        sort_columns = {
            "case_id": "c.case_id",
            "title": "c.title",
            "created_at": "c.created_at",
        }
        if sort_by not in sort_columns:
            raise ValueError("不支持的案例排序字段。")
        if sort_order not in {"asc", "desc"}:
            raise ValueError("不支持的案例排序方向。")

        predicates: list[str] = []
        parameters: list[object] = []
        normalized_query = query.strip() if query else ""
        if normalized_query:
            escaped_query = self._escape_like(normalized_query)
            predicates.append(
                "(c.case_id LIKE ? ESCAPE '\\' OR c.title LIKE ? ESCAPE '\\' "
                "OR ds.name LIKE ? ESCAPE '\\' OR COALESCE(c.activity_label, '') "
                "LIKE ? ESCAPE '\\')"
            )
            value = f"%{escaped_query}%"
            parameters.extend((value, value, value, value))
        if truth_category is not None:
            predicates.append("c.truth_category = ?")
            parameters.append(truth_category.value)
        if model_kind is not None:
            predicates.append(
                "EXISTS (SELECT 1 FROM json_each(c.allowed_models_json) "
                "WHERE json_each.value = ?)"
            )
            parameters.append(model_kind.value)

        where_clause = " WHERE " + " AND ".join(predicates) if predicates else ""
        order_clause = f" ORDER BY {sort_columns[sort_by]} {sort_order.upper()}, c.case_id ASC"
        offset = (page - 1) * page_size

        with self.connect() as connection:
            total = int(
                connection.execute(
                    "SELECT COUNT(*) FROM cases c "
                    "JOIN data_sources ds ON ds.source_id = c.source_id"
                    + where_clause,
                    parameters,
                ).fetchone()[0]
            )
            rows = connection.execute(
                "SELECT c.case_id, c.title, c.truth_category, ds.name AS source_name, "
                "ds.fixed_version, c.age_group, c.activity_label, "
                "c.allowed_models_json, c.created_at, "
                "COUNT(ss.stream_id) AS sensor_stream_count "
                "FROM cases c "
                "JOIN data_sources ds ON ds.source_id = c.source_id "
                "LEFT JOIN sensor_streams ss ON ss.case_id = c.case_id"
                + where_clause
                + " GROUP BY c.case_id, c.title, c.truth_category, ds.name, "
                "ds.fixed_version, c.age_group, c.activity_label, "
                "c.allowed_models_json, c.created_at"
                + order_clause
                + " LIMIT ? OFFSET ?",
                (*parameters, page_size, offset),
            ).fetchall()

        records = tuple(
            CaseListRecord(
                case_id=row["case_id"],
                title=row["title"],
                truth_category=row["truth_category"],
                source_name=row["source_name"],
                fixed_version=row["fixed_version"],
                age_group=row["age_group"],
                activity_label=row["activity_label"],
                allowed_models=tuple(json.loads(row["allowed_models_json"])),
                sensor_stream_count=int(row["sensor_stream_count"]),
                created_at=row["created_at"],
            )
            for row in rows
        )
        return records, total
