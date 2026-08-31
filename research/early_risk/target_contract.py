from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from research.early_risk.common import canonical_json_bytes, sha256_bytes


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceLevel(StrEnum):
    E0 = "E0"
    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"


class EventRole(StrEnum):
    PRIMARY_TARGET = "PRIMARY_TARGET"
    SECONDARY_TARGET = "SECONDARY_TARGET"
    HARD_NEGATIVE = "HARD_NEGATIVE"
    DEVICE_ARTIFACT = "DEVICE_ARTIFACT"


class TargetEventDefinition(ContractModel):
    code: NonEmptyText
    role: EventRole
    label_zh_cn: NonEmptyText
    operational_definition: NonEmptyText
    mutually_exclusive_with: tuple[NonEmptyText, ...]
    impact_required: bool


class TimeAnchorDefinition(ContractModel):
    code: NonEmptyText
    definition: NonEmptyText
    nullable: bool
    source_requirements: tuple[NonEmptyText, ...] = Field(min_length=1)


class EventMatchingSpec(ContractModel):
    maximum_pre_event_seconds: int = Field(gt=0)
    late_grace_seconds: int = Field(ge=0)
    duplicate_alert_merge_seconds: int = Field(gt=0)
    one_alert_matches_at_most_one_event: Literal[True] = True
    one_event_counted_at_most_once: Literal[True] = True
    negative_lead_time_is_late: Literal[True] = True


class ExternalApprovalState(ContractModel):
    product_owner_signed: bool
    research_owner_signed: bool
    safety_ethics_owner_signed: bool
    note: NonEmptyText


class TargetContract(ContractModel):
    contract_id: Literal["early-risk-target-contract"]
    version: Literal["1.0.0"]
    status: Literal["FROZEN_ENGINEERING_V1"]
    frozen_date: Literal["2026-08-31"]
    evidence_level: Literal[EvidenceLevel.E0] = EvidenceLevel.E0
    prediction_evidence: Literal[False] = False
    product_definition: NonEmptyText
    target_events: tuple[TargetEventDefinition, ...] = Field(min_length=1)
    time_anchors: tuple[TimeAnchorDefinition, ...] = Field(min_length=1)
    immediate_horizons_seconds: tuple[int, ...]
    background_horizons_hours: tuple[int, ...]
    primary_lead_time_formula: Literal[
        "t_instability - t_alert_perceivable"
    ]
    impact_lead_time_formula: Literal["t_impact - t_alert_perceivable"]
    synchronization_error_limit_ms: int = Field(gt=0, le=100)
    event_matching: EventMatchingSpec
    required_metric_ids: tuple[NonEmptyText, ...] = Field(min_length=1)
    allowed_e0_claims: tuple[NonEmptyText, ...] = Field(min_length=1)
    forbidden_claims: tuple[NonEmptyText, ...] = Field(min_length=1)
    external_approval_state: ExternalApprovalState

    @model_validator(mode="after")
    def validate_frozen_content(self) -> "TargetContract":
        expected_events = {
            "ACCIDENTAL_FALL",
            "NEAR_FALL",
            "INSTABILITY",
            "TRIP_RECOVERY",
            "RAPID_SIT",
            "INTENTIONAL_LIE_DOWN",
            "ORDINARY_TRANSITION",
            "DEVICE_ARTIFACT",
        }
        event_codes = {event.code for event in self.target_events}
        if event_codes != expected_events:
            raise ValueError("目标事件集合必须与 v1 冻结定义完全一致。")
        if len(event_codes) != len(self.target_events):
            raise ValueError("目标事件代码不能重复。")

        anchor_codes = {anchor.code for anchor in self.time_anchors}
        expected_anchors = {
            "t_instability",
            "t_impact",
            "t_recovery_or_assist",
            "t_model_decision",
            "t_alert_perceivable",
        }
        if anchor_codes != expected_anchors:
            raise ValueError("时间锚点集合必须与 v1 冻结定义完全一致。")
        if len(anchor_codes) != len(self.time_anchors):
            raise ValueError("时间锚点代码不能重复。")

        if self.immediate_horizons_seconds != (1, 2, 3, 5, 10):
            raise ValueError("数秒级评估时域必须固定为 1/2/3/5/10 秒。")
        if self.background_horizons_hours != (24, 168):
            raise ValueError("背景风险候选时域必须固定为 24 小时和 7 天。")

        required_metrics = {
            "event_recall_by_lead_time",
            "event_precision",
            "auprc",
            "false_alerts_per_person_day",
            "calibration",
            "lead_time_distribution",
            "coverage_and_abstention",
            "late_and_missed",
            "suppression_impact",
            "end_to_end_latency",
            "subgroup_and_robustness",
        }
        if set(self.required_metric_ids) != required_metrics:
            raise ValueError("强制指标集合不完整或包含未冻结指标。")
        if len(set(self.required_metric_ids)) != len(self.required_metric_ids):
            raise ValueError("强制指标不能重复。")

        normalized_allowed = "\n".join(self.allowed_e0_claims).lower()
        for claim in self.forbidden_claims:
            if claim.lower() in normalized_allowed:
                raise ValueError("E0 允许表述不能包含禁用能力声明。")
        return self


def load_target_contract(path: Path) -> TargetContract:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("目标合同 YAML 顶层必须是对象。")
    return TargetContract.model_validate(payload)


def target_contract_sha256(contract: TargetContract) -> str:
    return sha256_bytes(canonical_json_bytes(contract.model_dump(mode="json")))


def contract_completeness(contract: TargetContract) -> float:
    payload = contract.model_dump(mode="json")

    def count(value: object) -> tuple[int, int]:
        if isinstance(value, dict):
            totals = [count(item) for item in value.values()]
            return (sum(item[0] for item in totals), sum(item[1] for item in totals))
        if isinstance(value, list):
            totals = [count(item) for item in value]
            return (sum(item[0] for item in totals), sum(item[1] for item in totals))
        return (int(value is not None and value != ""), 1)

    present, total = count(payload)
    return present / total if total else 1.0
