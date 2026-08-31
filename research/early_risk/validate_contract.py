from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.early_risk.target_contract import (
    contract_completeness,
    load_target_contract,
    target_contract_sha256,
)


def build_validation_result(path: Path) -> dict[str, object]:
    contract = load_target_contract(path)
    return {
        "contract_id": contract.contract_id,
        "version": contract.version,
        "status": contract.status,
        "evidence_level": contract.evidence_level,
        "prediction_evidence": contract.prediction_evidence,
        "canonical_sha256": target_contract_sha256(contract),
        "required_field_completeness": contract_completeness(contract),
        "event_count": len(contract.target_events),
        "time_anchor_count": len(contract.time_anchors),
        "metric_count": len(contract.required_metric_ids),
        "formal_signoff_complete": all(
            (
                contract.external_approval_state.product_owner_signed,
                contract.external_approval_state.research_owner_signed,
                contract.external_approval_state.safety_ethics_owner_signed,
            )
        ),
        "meaning": "工程合同校验通过；不代表真实数据、伦理、模型有效性或报警获批。",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="校验 P0 提前风险目标合同。")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_validation_result(args.config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
