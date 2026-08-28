from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import (
    ContractModel,
    NonEmptyText,
    RoutineAssessment,
    RoutineEventContract,
    Sha256Hex,
)


class RoutineSlotRule(ContractModel):
    slot_key: NonEmptyText
    sample_count: int = Field(gt=0)
    start_mean_hour: float = Field(ge=0, lt=24)
    start_std_hour: float = Field(ge=0)
    start_interval_min_hour: float = Field(ge=0, lt=24)
    start_interval_max_hour: float = Field(gt=0, le=24)
    duration_mean_minutes: float = Field(gt=0)
    duration_std_minutes: float = Field(ge=0)
    duration_interval_min_minutes: float = Field(gt=0)
    duration_interval_max_minutes: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_intervals(self) -> "RoutineSlotRule":
        if self.start_interval_max_hour <= self.start_interval_min_hour:
            raise ValueError("规律开始时间上界必须晚于下界。")
        if self.duration_interval_max_minutes <= self.duration_interval_min_minutes:
            raise ValueError("规律时长上界必须大于下界。")
        return self


class RoutineTypeRule(ContractModel):
    event_type: Literal["meal", "nap", "walk"]
    daily_count_min: int = Field(ge=0)
    daily_count_max: int = Field(ge=0)
    slots: tuple[RoutineSlotRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_counts(self) -> "RoutineTypeRule":
        if self.daily_count_max < self.daily_count_min:
            raise ValueError("每日次数上界不能小于下界。")
        return self


class RoutineRulesArtifact(ContractModel):
    artifact_version: Literal["1.0.0"] = "1.0.0"
    profile_id: NonEmptyText
    history_days: Literal[100] = 100
    seed: int
    generator_source_commit: NonEmptyText
    source_archive_sha256: Sha256Hex
    source_archive_note: NonEmptyText
    std_multiplier: float = Field(gt=0)
    rules: tuple[RoutineTypeRule, ...] = Field(min_length=3, max_length=3)


def _hour(value: datetime) -> float:
    return value.hour + value.minute / 60 + value.second / 3600


class RoutineModelAdapter:
    def __init__(self, *, project_root: Path, manifest_path: Path) -> None:
        from ..contracts import ModelKind, ModelManifest

        self.project_root = project_root.resolve()
        self.manifest_path = manifest_path.resolve()
        self.manifest = ModelManifest.model_validate_json(
            self.manifest_path.read_text(encoding="utf-8")
        )
        if self.manifest.model_kind is not ModelKind.ROUTINE_ANOMALY:
            raise ValueError("规律适配器只能加载 ROUTINE_ANOMALY manifest。")
        if self.manifest.deployment_approved:
            raise ValueError("当前规律适配器只允许研究模型。")
        if self.manifest.artifact_relative_path is None:
            raise ValueError("规律模型 manifest 缺少规则文件。")
        artifact_path = (self.project_root / self.manifest.artifact_relative_path).resolve()
        if self.project_root not in artifact_path.parents:
            raise ValueError("规律规则文件必须位于项目目录内。")
        digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if digest != self.manifest.artifact_sha256:
            raise ValueError("规律规则文件哈希与 manifest 不一致。")
        self.artifact = RoutineRulesArtifact.model_validate_json(
            artifact_path.read_text(encoding="utf-8")
        )

    def assess_day(
        self,
        events: tuple[RoutineEventContract, ...],
    ) -> tuple[RoutineAssessment, ...]:
        if events and {event.profile_id for event in events} != {self.artifact.profile_id}:
            raise ValueError("规律事件的 profile_id 与规则不一致。")
        if events and len({event.started_at.date() for event in events}) != 1:
            raise ValueError("一次规律评估只能包含同一天的事件。")
        assessments: list[RoutineAssessment] = []
        for type_rule in self.artifact.rules:
            selected = sorted(
                (event for event in events if event.event_type == type_rule.event_type),
                key=lambda event: event.started_at,
            )
            count = len(selected)
            if count < type_rule.daily_count_min:
                assessments.append(
                    RoutineAssessment(
                        event_type=type_rule.event_type,
                        status="MISSING",
                        anomaly_score=1.0,
                        evidence=(
                            f"当天记录 {count} 次，合成历史范围为 "
                            f"{type_rule.daily_count_min}–{type_rule.daily_count_max} 次。",
                        ),
                    )
                )
                continue
            if count > type_rule.daily_count_max:
                assessments.append(
                    RoutineAssessment(
                        event_type=type_rule.event_type,
                        status="COUNT_DEVIATION",
                        anomaly_score=min(1.0, (count - type_rule.daily_count_max) / max(1, type_rule.daily_count_max)),
                        evidence=(
                            f"当天记录 {count} 次，超过合成历史上界 "
                            f"{type_rule.daily_count_max} 次。",
                        ),
                    )
                )
                continue

            by_slot = {event.slot_key: event for event in selected}
            candidates: list[tuple[float, str, str]] = []
            for slot in type_rule.slots:
                event = by_slot.get(slot.slot_key)
                if event is None:
                    continue
                start_hour = _hour(event.started_at)
                if start_hour < slot.start_interval_min_hour:
                    distance = slot.start_interval_min_hour - start_hour
                    score = min(1.0, distance / max(slot.start_std_hour, 0.25))
                    candidates.append(
                        (score, "EARLY", f"{slot.slot_key} 比合成规律下界早 {distance:.2f} 小时。")
                    )
                elif start_hour > slot.start_interval_max_hour:
                    distance = start_hour - slot.start_interval_max_hour
                    score = min(1.0, distance / max(slot.start_std_hour, 0.25))
                    candidates.append(
                        (score, "LATE", f"{slot.slot_key} 比合成规律上界晚 {distance:.2f} 小时。")
                    )
                elif event.duration_minutes < slot.duration_interval_min_minutes:
                    distance = slot.duration_interval_min_minutes - event.duration_minutes
                    score = min(1.0, distance / max(slot.duration_std_minutes, 5.0))
                    candidates.append(
                        (score, "DURATION_DEVIATION", f"{slot.slot_key} 时长比合成规律下界少 {distance:.1f} 分钟。")
                    )
                elif event.duration_minutes > slot.duration_interval_max_minutes:
                    distance = event.duration_minutes - slot.duration_interval_max_minutes
                    score = min(1.0, distance / max(slot.duration_std_minutes, 5.0))
                    candidates.append(
                        (score, "DURATION_DEVIATION", f"{slot.slot_key} 时长比合成规律上界多 {distance:.1f} 分钟。")
                    )

            if candidates:
                score, status, evidence = max(candidates, key=lambda item: item[0])
                assessments.append(
                    RoutineAssessment(
                        event_type=type_rule.event_type,
                        status=status,
                        anomaly_score=score,
                        evidence=(evidence,),
                    )
                )
            else:
                count_range = f"{type_rule.daily_count_min}–{type_rule.daily_count_max}"
                assessments.append(
                    RoutineAssessment(
                        event_type=type_rule.event_type,
                        status="WITHIN_ROUTINE",
                        anomaly_score=0.0,
                        evidence=(
                            f"当天 {count} 次，时间与时长均在 100 天合成规律内；"
                            f"允许次数为 {count_range} 次。",
                        ),
                    )
                )
        counts = Counter(item.event_type for item in assessments)
        if counts != {"meal": 1, "nap": 1, "walk": 1}:
            raise RuntimeError("规律模型必须独立返回 meal、nap、walk 三项评估。")
        return tuple(assessments)
