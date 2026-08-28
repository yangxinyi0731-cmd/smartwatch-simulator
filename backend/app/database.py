from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence

from .contracts import (
    CaseContract,
    CaseSourceFile,
    GroundTruthEvent,
    ImportRunContract,
    ModelKind,
    ModelManifest,
    SensorQualityContract,
    SensorStreamContract,
    SourceReference,
    TruthCategory,
)


SCHEMA_VERSION = 3

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

_SCHEMA_V3 = """
CREATE TABLE import_runs (
    run_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    importer_version TEXT NOT NULL CHECK (length(trim(importer_version)) > 0),
    source_commit TEXT NOT NULL CHECK (
        length(source_commit) IN (40, 64)
        AND source_commit NOT GLOB '*[^0-9a-f]*'
    ),
    processing_source_commit TEXT NOT NULL CHECK (
        length(processing_source_commit) IN (40, 64)
        AND processing_source_commit NOT GLOB '*[^0-9a-f]*'
    ),
    selection_policy_json TEXT NOT NULL CHECK (json_valid(selection_policy_json)),
    case_count INTEGER NOT NULL CHECK (case_count > 0),
    catalog_relative_path TEXT NOT NULL CHECK (
        length(trim(catalog_relative_path)) > 0
        AND substr(catalog_relative_path, 1, 1) NOT IN ('/', char(92))
        AND instr(catalog_relative_path, ':') = 0
        AND catalog_relative_path NOT LIKE '%..%'
    ),
    catalog_sha256 TEXT NOT NULL CHECK (
        length(catalog_sha256) = 64 AND catalog_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL
);

CREATE INDEX idx_import_runs_source_id ON import_runs (source_id, created_at DESC);

CREATE TABLE case_import_runs (
    run_id TEXT NOT NULL REFERENCES import_runs(run_id) ON DELETE RESTRICT,
    case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
    PRIMARY KEY (run_id, case_id)
);

CREATE INDEX idx_case_import_runs_case_id ON case_import_runs (case_id);

CREATE TABLE case_source_files (
    file_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
    role TEXT NOT NULL CHECK (role IN ('ACCELEROMETER', 'GYROSCOPE', 'ANNOTATION')),
    source_relative_path TEXT NOT NULL CHECK (
        length(trim(source_relative_path)) > 0
        AND substr(source_relative_path, 1, 1) NOT IN ('/', char(92))
        AND instr(source_relative_path, ':') = 0
        AND source_relative_path NOT LIKE '%..%'
    ),
    source_sha256 TEXT NOT NULL CHECK (
        length(source_sha256) = 64 AND source_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    UNIQUE (case_id, role, source_relative_path)
);

CREATE INDEX idx_case_source_files_case_id ON case_source_files (case_id);

CREATE TABLE sensor_quality (
    stream_id TEXT PRIMARY KEY REFERENCES sensor_streams(stream_id) ON DELETE RESTRICT,
    accel_rows INTEGER NOT NULL CHECK (accel_rows > 1),
    accel_unique_timestamps INTEGER NOT NULL CHECK (accel_unique_timestamps > 1),
    gyro_rows INTEGER NOT NULL CHECK (gyro_rows > 1),
    gyro_unique_timestamps INTEGER NOT NULL CHECK (gyro_unique_timestamps > 1),
    accel_effective_rate_hz REAL NOT NULL CHECK (accel_effective_rate_hz > 0),
    gyro_effective_rate_hz REAL NOT NULL CHECK (gyro_effective_rate_hz > 0),
    accel_median_dt_ms REAL NOT NULL CHECK (accel_median_dt_ms > 0),
    gyro_median_dt_ms REAL NOT NULL CHECK (gyro_median_dt_ms > 0),
    accel_max_gap_ms REAL NOT NULL CHECK (accel_max_gap_ms > 0),
    gyro_max_gap_ms REAL NOT NULL CHECK (gyro_max_gap_ms > 0),
    flags_json TEXT NOT NULL CHECK (
        json_valid(flags_json) AND json_type(flags_json) = 'array'
    )
);

CREATE TABLE ground_truth_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE RESTRICT,
    event_type TEXT NOT NULL CHECK (
        event_type IN ('ACTIVITY_INTERVAL', 'FALL_INTERVAL')
    ),
    label TEXT NOT NULL CHECK (length(trim(label)) > 0),
    start_offset_ms INTEGER NOT NULL CHECK (start_offset_ms >= 0),
    end_offset_ms INTEGER NOT NULL CHECK (end_offset_ms > start_offset_ms),
    truth_category TEXT NOT NULL CHECK (
        truth_category IN (
            'REAL_FREE_LIVING',
            'REAL_LAB_ACTIVITY',
            'SIMULATED_FALL',
            'SYNTHETIC_ROUTINE',
            'DERIVED_PERTURBATION'
        )
    ),
    annotation_source_sha256 TEXT NOT NULL CHECK (
        length(annotation_source_sha256) = 64
        AND annotation_source_sha256 NOT GLOB '*[^0-9a-f]*'
    ),
    notes TEXT NOT NULL CHECK (length(trim(notes)) > 0),
    CHECK (event_type <> 'FALL_INTERVAL' OR truth_category = 'SIMULATED_FALL')
);

CREATE INDEX idx_ground_truth_events_case_time
ON ground_truth_events (case_id, start_offset_ms, end_offset_ms);
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


@dataclass(frozen=True, slots=True)
class ImportCaseBundle:
    case: CaseContract
    stream: SensorStreamContract
    quality: SensorQualityContract
    source_files: tuple[CaseSourceFile, ...]
    ground_truth_events: tuple[GroundTruthEvent, ...]

    def __post_init__(self) -> None:
        case_id = self.case.case_id
        if self.stream.case_id != case_id or self.quality.stream_id != self.stream.stream_id:
            raise ValueError("案例、传感器流与质量记录的标识不一致。")
        if not self.source_files:
            raise ValueError("导入案例必须记录至少一个原始来源文件。")
        if not self.ground_truth_events:
            raise ValueError("导入案例必须记录至少一个真实标签事件。")
        if any(item.case_id != case_id for item in self.source_files):
            raise ValueError("原始来源文件必须属于同一个案例。")
        if any(item.case_id != case_id for item in self.ground_truth_events):
            raise ValueError("真实标签事件必须属于同一个案例。")


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
                current_version = 2

            if current_version < 3:
                self._apply_migration(connection, version=3, script=_SCHEMA_V3)

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

    @staticmethod
    def _json(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _timestamp(value: object) -> str:
        text = value.isoformat()
        return text.replace("+00:00", "Z")

    @staticmethod
    def _insert_or_verify(
        connection: sqlite3.Connection,
        *,
        table: str,
        key_column: str,
        values: dict[str, object],
    ) -> None:
        columns = tuple(values)
        placeholders = ", ".join("?" for _ in columns)
        connection.execute(
            f"INSERT OR IGNORE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(values[column] for column in columns),
        )
        row = connection.execute(
            f"SELECT {', '.join(columns)} FROM {table} WHERE {key_column} = ?",
            (values[key_column],),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"{table} 写入后无法读取。")
        mismatches = [
            column
            for column in columns
            if row[column] != values[column]
        ]
        if mismatches:
            joined = ", ".join(mismatches)
            raise ValueError(
                f"{table} 中标识 {values[key_column]!r} 已存在但内容冲突：{joined}。"
            )

    def import_case_bundles(
        self,
        *,
        source: SourceReference,
        import_run: ImportRunContract,
        bundles: Sequence[ImportCaseBundle],
    ) -> None:
        """Atomically import immutable, hash-addressed case metadata.

        Processed sensor files are created before this database call.  Database
        records are idempotent: a byte-for-byte-equivalent rerun is accepted,
        while a reused identifier with changed metadata aborts the transaction.
        """

        if import_run.source_id != source.source_id:
            raise ValueError("导入批次与数据来源标识不一致。")
        if len(bundles) != import_run.selection_policy.total_count:
            raise ValueError("实际案例数与分层选择策略声明不一致。")
        if len({bundle.case.case_id for bundle in bundles}) != len(bundles):
            raise ValueError("同一导入批次不能包含重复案例标识。")
        if any(bundle.case.source.source_id != source.source_id for bundle in bundles):
            raise ValueError("导入批次中的案例来源不一致。")

        source_values: dict[str, object] = {
            "source_id": source.source_id,
            "name": source.dataset_name,
            "source_url": str(source.source_url),
            "fixed_version": source.fixed_version,
            "license_status": source.license_status.value,
            "license_reference": source.license_reference,
            "redistribution_allowed": (
                None if source.redistribution_allowed is None else int(source.redistribution_allowed)
            ),
            "verified_at": self._timestamp(source.verified_at),
            "notes": source.notes,
        }
        run_values: dict[str, object] = {
            "run_id": import_run.run_id,
            "source_id": import_run.source_id,
            "importer_version": import_run.importer_version,
            "source_commit": import_run.source_commit,
            "processing_source_commit": import_run.processing_source_commit,
            "selection_policy_json": self._json(
                import_run.selection_policy.model_dump(mode="json")
            ),
            "case_count": len(bundles),
            "catalog_relative_path": import_run.catalog_relative_path,
            "catalog_sha256": import_run.catalog_sha256,
            "created_at": self._timestamp(import_run.created_at),
        }

        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._insert_or_verify(
                    connection,
                    table="data_sources",
                    key_column="source_id",
                    values=source_values,
                )
                self._insert_or_verify(
                    connection,
                    table="import_runs",
                    key_column="run_id",
                    values=run_values,
                )

                for bundle in bundles:
                    case = bundle.case
                    case_values: dict[str, object] = {
                        "case_id": case.case_id,
                        "title": case.title,
                        "description": case.description,
                        "truth_category": case.truth_category.value,
                        "source_id": case.source.source_id,
                        "source_record_path": case.source_record_path,
                        "source_sha256": case.source_sha256,
                        "participant_id": case.participant_id,
                        "age_group": case.age_group.value,
                        "device_name": case.device_name,
                        "wear_position": case.wear_position,
                        "original_sample_rate_hz": case.original_sample_rate_hz,
                        "activity_label": case.activity_label,
                        "has_accelerometer": int(case.has_accelerometer),
                        "has_gyroscope": int(case.has_gyroscope),
                        "allowed_models_json": self._json(
                            [model.value for model in case.allowed_models]
                        ),
                        "derivation_parent_case_id": case.derivation_parent_case_id,
                        "processing_command": case.processing_command,
                        "created_at": self._timestamp(case.created_at),
                        "updated_at": self._timestamp(case.updated_at),
                    }
                    self._insert_or_verify(
                        connection,
                        table="cases",
                        key_column="case_id",
                        values=case_values,
                    )
                    connection.execute(
                        "INSERT OR IGNORE INTO case_import_runs (run_id, case_id) VALUES (?, ?)",
                        (import_run.run_id, case.case_id),
                    )

                    stream = bundle.stream
                    stream_values: dict[str, object] = {
                        "stream_id": stream.stream_id,
                        "case_id": stream.case_id,
                        "sensor_kind": stream.sensor_kind.value,
                        "sample_rate_hz": stream.sample_rate_hz,
                        "channels_json": self._json(list(stream.channels)),
                        "units_json": self._json(list(stream.units)),
                        "sample_count": stream.sample_count,
                        "duration_ms": stream.duration_ms,
                        "storage_format": stream.storage_format.value,
                        "relative_path": stream.relative_path,
                        "content_sha256": stream.content_sha256,
                        "created_at": self._timestamp(stream.created_at),
                    }
                    self._insert_or_verify(
                        connection,
                        table="sensor_streams",
                        key_column="stream_id",
                        values=stream_values,
                    )

                    quality = bundle.quality
                    quality_values: dict[str, object] = {
                        "stream_id": quality.stream_id,
                        "accel_rows": quality.accel_rows,
                        "accel_unique_timestamps": quality.accel_unique_timestamps,
                        "gyro_rows": quality.gyro_rows,
                        "gyro_unique_timestamps": quality.gyro_unique_timestamps,
                        "accel_effective_rate_hz": quality.accel_effective_rate_hz,
                        "gyro_effective_rate_hz": quality.gyro_effective_rate_hz,
                        "accel_median_dt_ms": quality.accel_median_dt_ms,
                        "gyro_median_dt_ms": quality.gyro_median_dt_ms,
                        "accel_max_gap_ms": quality.accel_max_gap_ms,
                        "gyro_max_gap_ms": quality.gyro_max_gap_ms,
                        "flags_json": self._json(list(quality.flags)),
                    }
                    self._insert_or_verify(
                        connection,
                        table="sensor_quality",
                        key_column="stream_id",
                        values=quality_values,
                    )

                    for source_file in bundle.source_files:
                        self._insert_or_verify(
                            connection,
                            table="case_source_files",
                            key_column="file_id",
                            values={
                                "file_id": source_file.file_id,
                                "case_id": source_file.case_id,
                                "role": source_file.role.value,
                                "source_relative_path": source_file.source_relative_path,
                                "source_sha256": source_file.source_sha256,
                            },
                        )

                    for event in bundle.ground_truth_events:
                        self._insert_or_verify(
                            connection,
                            table="ground_truth_events",
                            key_column="event_id",
                            values={
                                "event_id": event.event_id,
                                "case_id": event.case_id,
                                "event_type": event.event_type.value,
                                "label": event.label,
                                "start_offset_ms": event.start_offset_ms,
                                "end_offset_ms": event.end_offset_ms,
                                "truth_category": event.truth_category.value,
                                "annotation_source_sha256": event.annotation_source_sha256,
                                "notes": event.notes,
                            },
                        )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def register_model_manifest(self, manifest: ModelManifest) -> None:
        values: dict[str, object] = {
            "manifest_id": manifest.manifest_id,
            "model_id": manifest.model_id,
            "model_kind": manifest.model_kind.value,
            "version": manifest.version,
            "format": manifest.format.value,
            "source_commit": manifest.source_commit,
            "artifact_relative_path": manifest.artifact_relative_path,
            "artifact_sha256": manifest.artifact_sha256,
            "contract_json": self._json(manifest.contract.model_dump(mode="json")),
            "training_provenance_json": self._json(
                {
                    "truth_categories": [
                        item.value for item in manifest.training_truth_categories
                    ],
                    "data_references": list(manifest.training_data_references),
                }
            ),
            "evaluation_json": self._json(
                {"reference": manifest.evaluation_reference}
            ),
            "limitations_json": self._json(list(manifest.limitations)),
            "deployment_approved": int(manifest.deployment_approved),
            "approval_status": manifest.approval_status.value,
            "external_validation_completed": int(
                manifest.external_validation_completed
            ),
            "created_at": self._timestamp(manifest.created_at),
        }
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._insert_or_verify(
                    connection,
                    table="model_manifests",
                    key_column="manifest_id",
                    values=values,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
