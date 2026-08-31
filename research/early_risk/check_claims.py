from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from research.early_risk.common import PROJECT_ROOT


ASSERTIVE_FORBIDDEN_PATTERNS = (
    re.compile(r"(?:已经|当前|现已)能提前预测"),
    re.compile(r"(?:已实现|已经实现)提前(?:预警|\s*\d+\s*秒)"),
    re.compile(r"临床级准确率\s*[:：]?\s*\d"),
    re.compile(r"自动救援已(?:启用|上线|完成)"),
    re.compile(r"真实老人提前(?:\s*\d+\s*秒)?.{0,12}(?:召回|精确率)\s*[:：]\s*\d"),
)


def scan_paths(paths: list[Path]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        current_level_two_heading = ""
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.startswith("## "):
                current_level_two_heading = line[3:].strip()
            if path.suffix.lower() == ".md" and (
                "禁用表述" in current_level_two_heading
                or any(marker in line for marker in ("不能", "不得", "禁止", "不代表"))
            ):
                continue
            for pattern in ASSERTIVE_FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                            "line": line_number,
                            "pattern": pattern.pattern,
                        }
                    )
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="扫描新增 E0 文档和报告中的越级能力声明。")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or list((PROJECT_ROOT / "docs" / "early_risk").glob("*.md"))
    paths += list((PROJECT_ROOT / "reports" / "early_risk").rglob("*.json"))
    unique_paths = sorted({path.resolve() for path in paths if path.is_file()})
    findings = scan_paths(unique_paths)
    print(
        json.dumps(
            {
                "scanned_file_count": len(unique_paths),
                "forbidden_assertion_count": len(findings),
                "findings": findings,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if findings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
