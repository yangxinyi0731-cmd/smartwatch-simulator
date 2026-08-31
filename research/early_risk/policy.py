from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence


class PolicyState(StrEnum):
    SILENT = "SILENT"
    ACCUMULATING = "ACCUMULATING"
    DRY_RUN_CANDIDATE = "DRY_RUN_CANDIDATE"
    COOLDOWN = "COOLDOWN"
    UNASSESSABLE = "UNASSESSABLE"
    SUPPRESSED = "SUPPRESSED"


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    threshold_on: float
    threshold_off: float
    consecutive_required: int
    cooldown_ms: int
    dry_run: bool = True

    def __post_init__(self) -> None:
        if not 0 <= self.threshold_off < self.threshold_on <= 1:
            raise ValueError("策略必须满足 0 <= threshold_off < threshold_on <= 1。")
        if self.consecutive_required <= 0 or self.cooldown_ms < 0:
            raise ValueError("连续证据数必须为正，冷却时长不能为负。")
        if not self.dry_run:
            raise ValueError("P2 策略只能运行 dry-run，禁止真实通知。")


@dataclass(frozen=True, slots=True)
class PolicyInput:
    timestamp_ms: int
    score: float
    evaluable: bool = True
    suppression_reason: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    timestamp_ms: int
    state: PolicyState
    evidence_count: int
    action: str
    reason: str
    external_notification_sent: bool = False


def run_dry_policy(
    inputs: Sequence[PolicyInput], config: PolicyConfig
) -> tuple[PolicyDecision, ...]:
    timestamps = [item.timestamp_ms for item in inputs]
    if any(right <= left for left, right in zip(timestamps, timestamps[1:])):
        raise ValueError("策略输入时间必须严格递增。")
    evidence_count = 0
    cooldown_until = -1
    decisions: list[PolicyDecision] = []
    for item in inputs:
        if not 0 <= item.score <= 1:
            raise ValueError("策略分数必须在 0–1。")
        if not item.evaluable:
            evidence_count = 0
            decisions.append(
                PolicyDecision(
                    timestamp_ms=item.timestamp_ms,
                    state=PolicyState.UNASSESSABLE,
                    evidence_count=0,
                    action="NONE",
                    reason="输入缺失、未知或质量不足，无法评估。",
                )
            )
            continue
        if item.suppression_reason is not None:
            evidence_count = 0
            decisions.append(
                PolicyDecision(
                    timestamp_ms=item.timestamp_ms,
                    state=PolicyState.SUPPRESSED,
                    evidence_count=0,
                    action="SUPPRESSED",
                    reason=item.suppression_reason,
                )
            )
            continue
        if item.timestamp_ms < cooldown_until:
            decisions.append(
                PolicyDecision(
                    timestamp_ms=item.timestamp_ms,
                    state=PolicyState.COOLDOWN,
                    evidence_count=0,
                    action="NONE",
                    reason="确定性冷却期内抑制重复候选。",
                )
            )
            continue
        if item.score >= config.threshold_on:
            evidence_count += 1
            if evidence_count >= config.consecutive_required:
                decisions.append(
                    PolicyDecision(
                        timestamp_ms=item.timestamp_ms,
                        state=PolicyState.DRY_RUN_CANDIDATE,
                        evidence_count=evidence_count,
                        action="RECORD_DRY_RUN_CANDIDATE",
                        reason="连续证据达到工程夹具阈值；只记录，不通知。",
                    )
                )
                evidence_count = 0
                cooldown_until = item.timestamp_ms + config.cooldown_ms
            else:
                decisions.append(
                    PolicyDecision(
                        timestamp_ms=item.timestamp_ms,
                        state=PolicyState.ACCUMULATING,
                        evidence_count=evidence_count,
                        action="NONE",
                        reason="正在累积确定性工程夹具证据。",
                    )
                )
            continue
        if item.score <= config.threshold_off:
            evidence_count = 0
        decisions.append(
            PolicyDecision(
                timestamp_ms=item.timestamp_ms,
                state=(
                    PolicyState.ACCUMULATING
                    if evidence_count
                    else PolicyState.SILENT
                ),
                evidence_count=evidence_count,
                action="NONE",
                reason="证据未达到 dry-run 候选条件。",
            )
        )
    return tuple(decisions)
