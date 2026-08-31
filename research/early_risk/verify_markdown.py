from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.early_risk.common import PROJECT_ROOT


def validate_markdown(path: Path) -> list[str]:
    findings: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    h1_count = 0
    previous_heading_level = 0
    fence_open = False
    for line_number, line in enumerate(lines, start=1):
        if "\t" in line:
            findings.append(f"line {line_number}: 包含 Tab。")
        if line.rstrip() != line:
            findings.append(f"line {line_number}: 包含行尾空白。")
        if line.startswith("```"):
            fence_open = not fence_open
            continue
        if fence_open or not line.startswith("#"):
            continue
        marker = line.split(" ", 1)[0]
        if set(marker) != {"#"} or len(marker) > 6:
            continue
        level = len(marker)
        if level == 1:
            h1_count += 1
        if previous_heading_level and level > previous_heading_level + 1:
            findings.append(
                f"line {line_number}: 标题从 H{previous_heading_level} 跳到 H{level}。"
            )
        previous_heading_level = level
    if h1_count != 1:
        findings.append(f"一级标题数量为 {h1_count}，必须为 1。")
    if fence_open:
        findings.append("代码围栏未闭合。")
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="检查提前风险 Markdown 结构与空白。")
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or sorted((PROJECT_ROOT / "docs" / "early_risk").glob("*.md"))
    resolved = [
        path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
        for path in paths
    ]
    findings = {
        str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"): validate_markdown(path)
        for path in resolved
    }
    failing = {path: items for path, items in findings.items() if items}
    print(
        json.dumps(
            {
                "checked_file_count": len(resolved),
                "failing_file_count": len(failing),
                "findings": failing,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if failing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
