from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.importers.weda import import_weda_cases


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从固定版本 WEDA-FALL 本机检出导入 100 个可追溯案例。"
    )
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument(
        "--database",
        type=Path,
        default=PROJECT_ROOT / "backend" / "runtime" / "smartwatch.sqlite3",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("data/catalog/weda_fall_100_v1.json"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.catalog.is_absolute():
        raise ValueError("--catalog 必须是项目内相对路径。")
    result = import_weda_cases(
        project_root=PROJECT_ROOT,
        raw_root=args.raw_root,
        database_path=args.database,
        catalog_relative_path=args.catalog,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
