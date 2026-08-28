from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1

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


@dataclass(frozen=True, slots=True)
class DatabaseSnapshot:
    schema_version: int
    case_count: int


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

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])

            if current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    "数据库结构版本高于当前程序支持的版本，已拒绝自动降级。"
                )

            if current_version < 1:
                with connection:
                    connection.executescript(_SCHEMA_V1)
                    connection.execute(
                        "INSERT OR IGNORE INTO schema_migrations (version, applied_at) "
                        "VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
                    )
                    connection.execute("PRAGMA user_version = 1")

    def snapshot(self) -> DatabaseSnapshot:
        with self.connect() as connection:
            connection.execute("SELECT 1").fetchone()
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            case_count = int(connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0])

        if schema_version != SCHEMA_VERSION:
            raise RuntimeError("数据库结构版本与当前程序不一致。")

        return DatabaseSnapshot(schema_version=schema_version, case_count=case_count)
