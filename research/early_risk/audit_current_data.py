from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.early_risk.common import PROJECT_ROOT, sha256_file, write_json_if_changed
from research.early_risk.reporting import E0Report
from research.early_risk.temporal import participant_overlap


DEFAULT_OUTPUT = PROJECT_ROOT / "reports" / "early_risk" / "e0" / "current_data_audit.json"


def _read_json(relative_path: str) -> dict[str, Any]:
    path = PROJECT_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{relative_path} 顶层必须是对象。")
    return payload


def _asset(relative_path: str) -> dict[str, object]:
    path = PROJECT_ROOT / relative_path
    return {
        "relative_path": relative_path.replace("\\", "/"),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_current_data_audit() -> E0Report:
    fall_manifest_path = "models/fall_detector/tcn_final_candidate/manifest.json"
    routine_manifest_path = "models/routine_anomaly/statistical_v1/manifest.json"
    activity_manifest_path = "models/activity_recognition/capture24_linear_v1/manifest.json"
    fall_report_path = "reports/models/fall_detector_tcn_100_cases.json"
    routine_report_path = "reports/models/routine_anomaly_scenarios.json"
    activity_report_path = "reports/models/activity_capture24_group_holdout.json"
    weda_catalog_path = "data/catalog/weda_fall_100_v1.json"
    capture_recovery_path = "data/catalog/capture24_recovered_prefix_v1.json"
    capture_selection_path = "data/catalog/capture24_activity_availability_v1.json"
    capture_training_path = "data/catalog/capture24_activity_training_v1.json"
    routine_data_path = "data/cases/synthetic_routine_100_v1.json"

    manifests = {
        "fall": _read_json(fall_manifest_path),
        "routine": _read_json(routine_manifest_path),
        "activity": _read_json(activity_manifest_path),
    }
    if any(manifest.get("deployment_approved") is not False for manifest in manifests.values()):
        raise ValueError("现有模型必须全部保持 deployment_approved=false。")
    if any(
        manifest.get("external_validation_completed") is not False
        for manifest in manifests.values()
    ):
        raise ValueError("现有模型不得伪装成已完成外部验证。")

    activity_report = _read_json(activity_report_path)
    split = activity_report["split"]
    overlap = participant_overlap(
        split["training_participants"], split["evaluation_participants"]
    )
    if overlap:
        raise ValueError(f"CAPTURE-24 保存拆分存在参与者交叉：{overlap}")

    weda_catalog = _read_json(weda_catalog_path)
    capture_recovery = _read_json(capture_recovery_path)
    routine_data = _read_json(routine_data_path)
    fall_report = _read_json(fall_report_path)
    routine_report = _read_json(routine_report_path)

    audited_paths = (
        fall_manifest_path,
        routine_manifest_path,
        activity_manifest_path,
        fall_report_path,
        routine_report_path,
        activity_report_path,
        weda_catalog_path,
        capture_recovery_path,
        capture_selection_path,
        capture_training_path,
        routine_data_path,
    )
    assets = [_asset(path) for path in audited_paths]
    usage_matrix = [
        {
            "asset_id": "weda-fall-100-v1",
            "truth_scope": "40 个年轻参与者受控模拟跌倒；30 个老人和 30 个年轻人受控日常活动。",
            "license_status": "UNVERIFIED",
            "allowed_use": ["事中/事后检测接线", "困难负样本发现", "软件回放与哈希核验"],
            "prohibited_use": ["真实老人跌倒召回", "数秒级提前预测", "公开重分发或商用"],
            "record_count": weda_catalog["case_count"],
        },
        {
            "asset_id": "capture24-recovered-prefix-v1",
            "truth_scope": "官方不完整下载前缀中逐成员核验的 48 人自由生活子集；主要不是老人。",
            "license_status": "CC_BY_4_0_DATA__TOOL_CODE_SEPARATE",
            "allowed_use": ["活动上下文", "参与者隔离管线", "三轴窗口工程烟测"],
            "prohibited_use": ["完整 151 人数据包", "老人专项活动验证", "跌倒或预事件外部验证"],
            "participant_count": capture_recovery["participant_count"],
            "saved_split_overlap": list(overlap),
        },
        {
            "asset_id": "synthetic-routine-100-v1",
            "truth_scope": "固定种子生成的 100 天合成用餐、午睡和散步事件。",
            "license_status": "PROJECT_GENERATED_FIXTURE",
            "allowed_use": ["规则分支", "合同", "解释和确定性测试"],
            "prohibited_use": ["真实个人基线", "医学风险概率", "真实世界预测成绩"],
            "event_count": routine_data["event_count"],
        },
    ]
    return E0Report(
        report_id="early-risk-current-data-audit-v1",
        generated_from=tuple(audited_paths),
        claims=(
            "现有资产的允许用途、禁止用途、许可状态和哈希已完成离线审计。",
            "三个现有模型仅登记为职责受限比较基线，均未获部署批准。",
        ),
        limitations=(
            "本审计没有下载新数据，也没有读取或写入真实个人数据。",
            "WEDA-FALL 许可仍为 UNVERIFIED，不能默认允许重分发或商用。",
            "现有报告不提供真实老人提前数秒预测、自然生活误报/人日或外部验证证据。",
        ),
        results={
            "no_download_performed": True,
            "audited_asset_count": len(assets),
            "expected_asset_count": len(audited_paths),
            "asset_coverage": len(assets) / len(audited_paths),
            "assets": assets,
            "usage_matrix": usage_matrix,
            "model_registry": [
                {
                    "model_kind": manifest["model_kind"],
                    "version": manifest["version"],
                    "artifact_sha256": manifest.get("artifact_sha256"),
                    "external_validation_completed": manifest[
                        "external_validation_completed"
                    ],
                    "deployment_approved": manifest["deployment_approved"],
                    "limitations": manifest["limitations"],
                }
                for manifest in manifests.values()
            ],
            "saved_report_facts": {
                "fall_replay_case_count": fall_report["dataset"]["case_count"],
                "fall_replay_false_alarm_episodes": fall_report["event_metrics"][
                    "false_alarm_episodes"
                ],
                "routine_scenario_count": routine_report["scenario_count"],
                "routine_passed_scenario_count": routine_report[
                    "passed_scenario_count"
                ],
                "activity_evaluation_windows": activity_report["evaluation"][
                    "window_count"
                ],
                "activity_participant_overlap": list(overlap),
                "interpretation": "仅重述已保存报告的受限范围，不转换为提前预测成绩。",
            },
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="只读审计当前数据和模型资产。")
    parser.add_argument("--no-download", action="store_true", required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = build_current_data_audit()
    write_json_if_changed(args.output, report.model_dump(mode="json"))
    print(args.output.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
