from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "backend" / "runtime" / "smartwatch.sqlite3"


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path

    @classmethod
    def from_environment(cls) -> "Settings":
        configured_path = os.getenv("SMARTWATCH_DATABASE_PATH")
        if configured_path:
            database_path = Path(configured_path).expanduser()
            if not database_path.is_absolute():
                raise ValueError("SMARTWATCH_DATABASE_PATH 必须是绝对路径。")
        else:
            database_path = DEFAULT_DATABASE_PATH

        return cls(database_path=database_path.resolve())
