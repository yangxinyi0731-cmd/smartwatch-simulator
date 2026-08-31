from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.early_risk.common import PROJECT_ROOT, pretty_json_text
from research.early_risk.contracts import (
    EventAnnotation,
    ResearchRecordBundle,
    SensorProfile,
    SensorSegment,
    WithdrawalIndexEntry,
)


OUTPUT_PATH = PROJECT_ROOT / "docs" / "contracts" / "early-risk-domain.schema.json"


def build_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "提前风险研究统一数据合同",
        "contract_version": "1.0.0",
        "evidence_level": "E0",
        "prediction_evidence": False,
        "schemas": {
            "SensorProfile": SensorProfile.model_json_schema(),
            "SensorSegment": SensorSegment.model_json_schema(),
            "EventAnnotation": EventAnnotation.model_json_schema(),
            "ResearchRecordBundle": ResearchRecordBundle.model_json_schema(),
            "WithdrawalIndexEntry": WithdrawalIndexEntry.model_json_schema(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="导出或检查提前风险 P1 JSON Schema。")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = pretty_json_text(build_schema())
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != expected:
            raise SystemExit("early-risk-domain.schema.json 与代码合同漂移。")
        print(OUTPUT_PATH.relative_to(PROJECT_ROOT))
        return
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(expected, encoding="utf-8")
    print(OUTPUT_PATH.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
