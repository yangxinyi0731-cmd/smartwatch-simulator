from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BaselineRole(StrEnum):
    INTEGRITY = "INTEGRITY"
    MOTION_HEURISTIC = "MOTION_HEURISTIC"
    DURING_OR_AFTER_EVENT = "DURING_OR_AFTER_EVENT"
    SYNTHETIC_SOFTWARE = "SYNTHETIC_SOFTWARE"
    ACTIVITY_CONTEXT = "ACTIVITY_CONTEXT"


@dataclass(frozen=True, slots=True)
class BaselineRegistration:
    baseline_id: str
    role: BaselineRole
    allowed_use: str
    prohibited_interpretation: str
    evidence_level: str = "E0"
    prediction_evidence: bool = False
    deployment_approved: bool = False


def baseline_registry() -> tuple[BaselineRegistration, ...]:
    return (
        BaselineRegistration(
            baseline_id="never_alert",
            role=BaselineRole.INTEGRITY,
            allowed_use="验证漏报、覆盖率和指标分母。",
            prohibited_interpretation="不能作为安全策略或低风险证明。",
        ),
        BaselineRegistration(
            baseline_id="always_alert",
            role=BaselineRole.INTEGRITY,
            allowed_use="验证事件召回上界和误报负担公式。",
            prohibited_interpretation="不能作为可用报警策略。",
        ),
        BaselineRegistration(
            baseline_id="simple_motion_threshold",
            role=BaselineRole.MOTION_HEURISTIC,
            allowed_use="在确定性夹具上验证阈值、事件合并和状态机。",
            prohibited_interpretation="不能产生真实老人提前预测成绩。",
        ),
        BaselineRegistration(
            baseline_id="existing_fall_detector",
            role=BaselineRole.DURING_OR_AFTER_EVENT,
            allowed_use="事中/事后检测比较、困难负样本发现和事件确认候选。",
            prohibited_interpretation="不能直接称为短时前兆或未来跌倒模型。",
        ),
        BaselineRegistration(
            baseline_id="synthetic_routine_rules",
            role=BaselineRole.SYNTHETIC_SOFTWARE,
            allowed_use="验证合成规则、合同和解释分支。",
            prohibited_interpretation="异常分数不是医学风险或真实跌倒概率。",
        ),
        BaselineRegistration(
            baseline_id="activity_context",
            role=BaselineRole.ACTIVITY_CONTEXT,
            allowed_use="活动上下文、特征探索和数据管线比较。",
            prohibited_interpretation="不能证明老人目标域有效或提前预测有效。",
        ),
    )
