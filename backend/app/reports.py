from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from .contracts import ModelKind
from .database import ModelListRecord
from .schemas import ReportListResponse, ReportMetric, ReportSummaryItem


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_REPORT_PATHS = {
    ModelKind.FALL_DETECTION: "reports/models/fall_detector_tcn_100_cases.json",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _report_path(relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("评估报告路径必须是项目内安全相对路径。")
    resolved = (PROJECT_ROOT / candidate).resolve()
    if not resolved.is_relative_to(PROJECT_ROOT) or not resolved.is_file():
        raise ValueError("已登记评估报告不存在或不在项目目录内。")
    return resolved


def _metric(
    key: str,
    label: str,
    display_value: str,
    *,
    numeric_value: float | int | None = None,
    interpretation: str,
) -> ReportMetric:
    return ReportMetric(
        key=key,
        label=label,
        display_value=display_value,
        numeric_value=numeric_value,
        interpretation=interpretation,
    )


def _fall_metrics(payload: dict[str, object]) -> tuple[ReportMetric, ...]:
    dataset = payload["dataset"]
    event = payload["event_metrics"]
    older = payload["older_adl_false_alarm_analysis"]
    if not isinstance(dataset, dict) or not isinstance(event, dict) or not isinstance(older, dict):
        raise ValueError("跌倒评估报告结构不完整。")
    case_count = int(dataset["case_count"])
    true_positive = int(event["true_positive_simulated_fall_events"])
    false_negative = int(event["false_negative_simulated_fall_events"])
    false_alarm = int(event["false_alarm_episodes"])
    older_count = int(older["case_count"])
    older_false_alarm = int(older["false_alarm_episodes"])
    return (
        _metric(
            "evaluated_cases",
            "同源重放案例",
            f"{case_count} 个",
            numeric_value=case_count,
            interpretation="40 个年轻参与者受控模拟跌倒，60 个受控日常活动。",
        ),
        _metric(
            "simulated_fall_alert_overlap",
            "模拟跌倒出现重叠告警",
            f"{true_positive} / {true_positive + false_negative}",
            numeric_value=true_positive,
            interpretation="仅表示告警时间段与受控模拟跌倒标签重叠。",
        ),
        _metric(
            "false_negative_simulated_falls",
            "模拟跌倒漏报告警",
            f"{false_negative} 个",
            numeric_value=false_negative,
            interpretation="不代表对真实老人跌倒的漏报率。",
        ),
        _metric(
            "adl_false_alarm_episodes",
            "日常活动误报告警段",
            f"{false_alarm} 段",
            numeric_value=false_alarm,
            interpretation="来自 60 个受控日常活动案例的同源重放。",
        ),
        _metric(
            "older_adl_false_alarm_episodes",
            "老人日常活动误报告警段",
            f"{older_false_alarm} 段 / {older_count} 个案例",
            numeric_value=older_false_alarm,
            interpretation="老人参与者只执行日常活动；数据中没有老人跌倒。",
        ),
    )


def _routine_metrics(payload: dict[str, object]) -> tuple[ReportMetric, ...]:
    history = payload["history"]
    if not isinstance(history, dict):
        raise ValueError("规律评估报告结构不完整。")
    scenario_count = int(payload["scenario_count"])
    passed = int(payload["passed_scenario_count"])
    history_days = int(history["history_days"])
    event_count = int(history["event_count"])
    return (
        _metric(
            "rule_scenarios_passed",
            "确定性规则场景",
            f"{passed} / {scenario_count} 通过",
            numeric_value=passed,
            interpretation="核验保存规则的预期分支，不是准确率或召回率。",
        ),
        _metric(
            "synthetic_history_days",
            "合成规律长度",
            f"{history_days} 天",
            numeric_value=history_days,
            interpretation="固定种子生成，不代表真实老人生活记录。",
        ),
        _metric(
            "synthetic_event_count",
            "合成事件",
            f"{event_count} 条",
            numeric_value=event_count,
            interpretation="只包含用餐、午睡与散步演示事件。",
        ),
    )


def _activity_metrics(payload: dict[str, object]) -> tuple[ReportMetric, ...]:
    evaluation = payload["evaluation"]
    split = payload["split"]
    if not isinstance(evaluation, dict) or not isinstance(split, dict):
        raise ValueError("活动评估报告结构不完整。")
    metrics = evaluation["participant_group_holdout_metrics"]
    if not isinstance(metrics, dict):
        raise ValueError("活动评估指标结构不完整。")
    window_count = int(evaluation["window_count"])
    accuracy = float(metrics["accuracy"])
    macro_f1 = float(metrics["macro_f1"])
    evaluation_participants = split["evaluation_participants"]
    if not isinstance(evaluation_participants, list):
        raise ValueError("活动评估参与者清单结构不完整。")
    return (
        _metric(
            "evaluation_windows",
            "留出参与者窗口",
            f"{window_count} 个",
            numeric_value=window_count,
            interpretation=f"来自 {len(evaluation_participants)} 名固定评估参与者。",
        ),
        _metric(
            "participant_holdout_accuracy",
            "参与者分组留出准确率",
            f"{accuracy * 100:.1f}%",
            numeric_value=accuracy,
            interpretation="同一 CAPTURE-24 数据集内的未见参与者组，不是外部验证。",
        ),
        _metric(
            "participant_holdout_macro_f1",
            "参与者分组留出宏平均 F1",
            f"{macro_f1:.3f}",
            numeric_value=macro_f1,
            interpretation="只适用于保存的四类映射、窗口上限和处理配置。",
        ),
    )


def _summary(record: ModelListRecord) -> ReportSummaryItem:
    model_kind = ModelKind(record.model_kind)
    relative_path = PLATFORM_REPORT_PATHS.get(
        model_kind,
        record.evaluation_reference,
    )
    path = _report_path(relative_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("评估报告根节点必须是对象。")
    if model_kind is ModelKind.FALL_DETECTION:
        title = "跌倒检测同源 100 案例重放"
        scope = "same_source_behavior_replay"
        scope_note = (
            "WEDA 同一来源上的接线与行为核验；受控模拟跌倒不是实际老人跌倒，"
            "也不是独立泛化评估。"
        )
        metrics = _fall_metrics(payload)
    elif model_kind is ModelKind.ROUTINE_ANOMALY:
        title = "生活规律确定性规则场景核验"
        scope = "deterministic_rule_scenarios"
        scope_note = (
            "固定种子合成事件上的规则分支核验；不计算真实世界准确率、召回率或医学风险。"
        )
        metrics = _routine_metrics(payload)
    elif model_kind is ModelKind.ACTIVITY_RECOGNITION:
        title = "腕部活动参与者分组留出评估"
        scope = "same_dataset_participant_holdout"
        scope_note = (
            "CAPTURE-24 同一数据集内不重叠参与者组评估；该数据以年轻参与者为主，"
            "不是老人数据，也不是独立外部验证。"
        )
        metrics = _activity_metrics(payload)
    else:  # pragma: no cover - ModelKind currently has exactly three values.
        raise ValueError("未知模型类型。")
    return ReportSummaryItem(
        report_id=f"{record.manifest_id}-evaluation",
        manifest_id=record.manifest_id,
        model_kind=model_kind,
        title=title,
        evidence_scope=scope,
        evidence_scope_note=scope_note,
        report_relative_path=relative_path,
        report_sha256=_sha256(path),
        metrics=metrics,
        limitations=record.limitations,
        deployment_approved=record.deployment_approved,
        external_validation_completed=record.external_validation_completed,
        created_at=record.created_at,
    )


def build_report_list(records: tuple[ModelListRecord, ...]) -> ReportListResponse:
    items = tuple(_summary(record) for record in records)
    return ReportListResponse(
        items=items,
        total=len(items),
        generated_at=datetime.now(UTC),
        disclaimers=(
            "三个模型独立报告，不合并成综合医学风险分数。",
            "所有模型均为研究演示，未完成外部验证，deployment_approved=false。",
            "年轻参与者受控模拟跌倒不得描述为真实老人跌倒。",
        ),
    )
