from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from research.early_risk.common import PROJECT_ROOT


DEFAULT_DATABASE = PROJECT_ROOT / "backend" / "runtime" / "smartwatch.sqlite3"


def read_runtime_state(database_path: Path) -> dict[str, object]:
    resolved = database_path.resolve()
    connection = sqlite3.connect(
        f"file:{resolved.as_posix()}?mode=ro&immutable=1", uri=True
    )
    try:
        scalar = lambda statement: connection.execute(statement).fetchone()[0]
        batch_columns = tuple(
            row[1] for row in connection.execute("PRAGMA table_info(batch_replay_tasks)")
        )
        state_column = next(
            (name for name in ("state", "status", "task_state") if name in batch_columns),
            None,
        )
        completed_batch_tasks = (
            scalar(
                f"SELECT COUNT(*) FROM batch_replay_tasks WHERE {state_column} = 'COMPLETED'"
            )
            if state_column is not None
            else None
        )
        return {
            "database_path": str(resolved),
            "open_mode": "read_only",
            "immutable": True,
            "integrity": scalar("PRAGMA integrity_check"),
            "schema_version": scalar("PRAGMA user_version"),
            "cases": scalar("SELECT COUNT(*) FROM cases"),
            "models": scalar("SELECT COUNT(*) FROM model_manifests"),
            "batch_tasks": scalar("SELECT COUNT(*) FROM batch_replay_tasks"),
            "completed_batch_tasks": completed_batch_tasks,
            "batch_state_column": state_column,
        }
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="只读核对现有 SQLite 运行基线。")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    args = parser.parse_args()
    print(json.dumps(read_runtime_state(args.database), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
