from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.early_risk.audit_current_data import (
    DEFAULT_OUTPUT as DATA_AUDIT_PATH,
    build_current_data_audit,
)
from research.early_risk.check_claims import scan_paths
from research.early_risk.common import (
    PROJECT_ROOT,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
    write_json_if_changed,
)
from research.early_risk.export_contracts import OUTPUT_PATH as SCHEMA_PATH
from research.early_risk.export_contracts import build_schema
from research.early_risk.reporting import E0Report
from research.early_risk.run_fixture_benchmark import (
    DEFAULT_CONFIG,
    DEFAULT_FIXTURE,
    DEFAULT_OUTPUT as FIXTURE_REPORT_PATH,
    build_fixture_report,
)
from research.early_risk.validate_contract import build_validation_result


TARGET_CONTRACT_PATH = PROJECT_ROOT / "configs" / "early_risk" / "target_contract.v1.yaml"
DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "early_risk" / "e0" / "p0_p2_gate_summary.json"


def build_gate_report() -> E0Report:
    contract_result = build_validation_result(TARGET_CONTRACT_PATH)
    committed_schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    schema_drift = committed_schema != build_schema()

    data_audit = build_current_data_audit()
    committed_data_audit = json.loads(DATA_AUDIT_PATH.read_text(encoding="utf-8"))
    data_audit_drift = committed_data_audit != data_audit.model_dump(mode="json")

    first_fixture = build_fixture_report(DEFAULT_CONFIG, DEFAULT_FIXTURE)
    second_fixture = build_fixture_report(DEFAULT_CONFIG, DEFAULT_FIXTURE)
    first_bytes = canonical_json_bytes(first_fixture.model_dump(mode="json"))
    second_bytes = canonical_json_bytes(second_fixture.model_dump(mode="json"))
    committed_fixture = json.loads(FIXTURE_REPORT_PATH.read_text(encoding="utf-8"))
    fixture_report_drift = committed_fixture != first_fixture.model_dump(mode="json")

    documentation_paths = sorted((PROJECT_ROOT / "docs" / "early_risk").glob("*.md"))
    documentation_paths += sorted((PROJECT_ROOT / "reports" / "early_risk").rglob("*.json"))
    forbidden_findings = scan_paths(documentation_paths)

    engineering_pass = all(
        (
            contract_result["required_field_completeness"] == 1.0,
            not schema_drift,
            not data_audit_drift,
            not fixture_report_drift,
            first_bytes == second_bytes,
            first_fixture.results["temporal_leakage"]["finding_count"] == 0,
            first_fixture.results["policy"]["external_notification_count"] == 0,
            data_audit.results["asset_coverage"] == 1.0,
            not forbidden_findings,
        )
    )
    if not engineering_pass:
        raise ValueError("P0–P2 工程 Gate 证据不一致，拒绝生成通过报告。")

    return E0Report(
        report_id="early-risk-p0-p2-gate-summary-v1",
        generated_from=(
            "configs/early_risk/target_contract.v1.yaml",
            "docs/contracts/early-risk-domain.schema.json",
            "reports/early_risk/e0/current_data_audit.json",
            "reports/early_risk/e0/fixture_benchmark.json",
        ),
        claims=(
            "P0、P1、P2 的工程合同、数据合同、资产审计和确定性离线骨架满足 E0 Gate。",
            "本 Gate 只授权表述离线研究骨架可重复运行。",
        ),
        limitations=(
            "正式产品、研究和安全/伦理负责人签署仍未完成。",
            "没有接入真实个人数据、训练提前预测模型、运行风险 UI、发送通知或部署。",
            "本报告不能证明真实老人提前预测能力，不能授权进入 P3 或任何报警阶段。",
        ),
        results={
            "overall": {
                "engineering_status": "PASS_E0_FOUNDATION",
                "next_stage_authorized": False,
                "formal_signoff_complete": contract_result["formal_signoff_complete"],
            },
            "p0": {
                "status": "ENGINEERING_PASS__FORMAL_SIGNOFF_PENDING",
                "contract_completeness": contract_result[
                    "required_field_completeness"
                ],
                "contract_canonical_sha256": contract_result["canonical_sha256"],
                "event_count": contract_result["event_count"],
                "time_anchor_count": contract_result["time_anchor_count"],
                "required_metric_count": contract_result["metric_count"],
                "forbidden_assertion_count": len(forbidden_findings),
            },
            "p1": {
                "status": "ENGINEERING_PASS",
                "schema_drift": schema_drift,
                "schema_sha256": sha256_file(SCHEMA_PATH),
                "synchronization_error_limit_ms": 100,
                "negative_fixture_suite": "tests/early_risk/test_contracts.py",
            },
            "p2": {
                "status": "ENGINEERING_PASS_E0_ONLY",
                "data_asset_coverage": data_audit.results["asset_coverage"],
                "audited_asset_count": data_audit.results["audited_asset_count"],
                "participant_overlap": data_audit.results["saved_report_facts"][
                    "activity_participant_overlap"
                ],
                "temporal_leakage_finding_count": first_fixture.results[
                    "temporal_leakage"
                ]["finding_count"],
                "fixture_repeat_hashes_identical": first_bytes == second_bytes,
                "fixture_canonical_sha256": sha256_bytes(first_bytes),
                "external_notification_count": first_fixture.results["policy"][
                    "external_notification_count"
                ],
                "data_audit_sha256": sha256_file(DATA_AUDIT_PATH),
                "fixture_report_sha256": sha256_file(FIXTURE_REPORT_PATH),
            },
            "required_external_actions_before_p3": [
                "产品、研究和安全/伦理负责人正式签署目标合同",
                "伦理、知情同意、数据控制和许可决定",
                "用户另行明确授权进入 P3",
            ],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 P0–P2 E0 Gate 汇总证据。")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    report = build_gate_report()
    write_json_if_changed(output, report.model_dump(mode="json"))
    print(output.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
