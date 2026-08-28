from __future__ import annotations

from datetime import date, datetime
from math import ceil
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts import (
    AgeGroup,
    ActivityProbabilities,
    ApprovalStatus,
    CaseContract,
    GroundTruthEvent,
    ManifestFormat,
    ModelKind,
    RoutineAssessment,
    RoutineEventContract,
    SensorQualityContract,
    SensorStreamContract,
    TruthCategory,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServiceHealth(ApiModel):
    name: str = "smartwatch-health-simulator"
    version: str
    state: Literal["ready", "degraded"]


class DatabaseHealth(ApiModel):
    engine: Literal["sqlite"] = "sqlite"
    state: Literal["ready", "unavailable"]
    schema_version: int | None = Field(default=None, ge=1)


class CaseSummary(ApiModel):
    count: int | None = Field(default=None, ge=0)
    state: Literal["empty", "available", "unavailable"]


class RealtimeHealth(ApiModel):
    transport: Literal["websocket"] = "websocket"
    path: str = "/ws/system"


class SystemStatus(ApiModel):
    event: Literal["system.status"] = "system.status"
    service: ServiceHealth
    database: DatabaseHealth
    cases: CaseSummary
    realtime: RealtimeHealth = Field(default_factory=RealtimeHealth)
    checked_at: datetime
    message: str


class ApiError(ApiModel):
    code: str
    message: str
    retryable: bool


class CaseListItem(ApiModel):
    case_id: str
    title: str
    truth_category: TruthCategory
    source_name: str
    fixed_version: str
    age_group: AgeGroup
    activity_label: str | None
    allowed_models: tuple[ModelKind, ...]
    sensor_stream_count: int = Field(ge=0)
    created_at: datetime


class CaseListResponse(ApiModel):
    items: tuple[CaseListItem, ...]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    @classmethod
    def from_page(
        cls,
        *,
        items: tuple[CaseListItem, ...],
        page: int,
        page_size: int,
        total: int,
    ) -> "CaseListResponse":
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    @model_validator(mode="after")
    def validate_page_bounds(self) -> "CaseListResponse":
        if self.total == 0:
            if self.page != 1 or self.total_pages != 0 or self.items:
                raise ValueError("空案例库必须停留在第 1 页并返回 0 页。")
        elif self.page > self.total_pages:
            raise ValueError("案例页码不能超过总页数。")
        return self


class ModelListItem(ApiModel):
    manifest_id: str
    model_id: str
    model_kind: ModelKind
    version: str
    format: ManifestFormat
    source_commit: str
    artifact_relative_path: str | None
    artifact_sha256: str | None
    training_truth_categories: tuple[TruthCategory, ...]
    evaluation_reference: str
    limitations: tuple[str, ...]
    deployment_approved: bool
    approval_status: ApprovalStatus
    external_validation_completed: bool
    created_at: datetime


class ModelListResponse(ApiModel):
    items: tuple[ModelListItem, ...]
    total: int = Field(ge=0)


class ReportMetric(ApiModel):
    key: str
    label: str
    display_value: str
    numeric_value: float | int | None
    interpretation: str


class ReportSummaryItem(ApiModel):
    report_id: str
    manifest_id: str
    model_kind: ModelKind
    title: str
    evidence_scope: Literal[
        "same_source_behavior_replay",
        "deterministic_rule_scenarios",
        "same_dataset_participant_holdout",
    ]
    evidence_scope_note: str
    report_relative_path: str
    report_sha256: str
    metrics: tuple[ReportMetric, ...]
    limitations: tuple[str, ...]
    deployment_approved: bool
    external_validation_completed: bool
    created_at: datetime


class ReportListResponse(ApiModel):
    items: tuple[ReportSummaryItem, ...]
    total: int = Field(ge=0)
    generated_at: datetime
    disclaimers: tuple[str, ...]


class SensorSamplePoint(ApiModel):
    offset_ms: int = Field(ge=0)
    values: tuple[float, ...] = Field(min_length=1)


class FallWindowResult(ApiModel):
    start_offset_ms: int = Field(ge=0)
    end_offset_ms: int = Field(gt=0)
    fall_probability: float = Field(ge=0, le=1)
    is_candidate: bool


class FallAlarmEpisodeItem(ApiModel):
    start_offset_ms: int = Field(ge=0)
    end_offset_ms: int = Field(gt=0)
    peak_probability: float = Field(ge=0, le=1)
    window_count: int = Field(gt=0)


class RoutineProfileSummary(ApiModel):
    profile_id: str
    history_days: int = Field(gt=0)
    history_start: date
    history_end: date
    seed: int
    event_count: int = Field(gt=0)
    events_sha256: str


class RoutineDayResult(ApiModel):
    day: date
    events: tuple[RoutineEventContract, ...]
    assessments: tuple[RoutineAssessment, ...]


class ActivityPreviewResult(ApiModel):
    manifest_id: str
    probabilities: ActivityProbabilities
    predicted_label: Literal[
        "walking", "eating_candidate", "sleep_or_lying_candidate", "other_unknown"
    ]
    deployment_approved: Literal[False] = False


class ReplayPreviewResponse(ApiModel):
    case: CaseContract
    duration_ms: int = Field(ge=0)
    sensor_stream: SensorStreamContract | None
    sensor_quality: SensorQualityContract | None
    ground_truth_events: tuple[GroundTruthEvent, ...]
    sensor_samples: tuple[SensorSamplePoint, ...]
    fall_manifest_id: str | None
    fall_threshold: float | None = Field(default=None, ge=0, le=1)
    fall_windows: tuple[FallWindowResult, ...]
    fall_alarm_episodes: tuple[FallAlarmEpisodeItem, ...]
    routine_profile: RoutineProfileSummary | None
    routine_days: tuple[RoutineDayResult, ...]
    activity_result: ActivityPreviewResult | None
    messages: tuple[str, ...]
    generated_at: datetime


BatchReplayTaskState = Literal[
    "QUEUED",
    "RUNNING",
    "COMPLETED",
    "COMPLETED_WITH_ERRORS",
    "FAILED",
]
BatchReplayItemState = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED"]


class BatchReplayCreateRequest(ApiModel):
    client_request_id: str = Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]+$",
    )
    case_ids: tuple[str, ...] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_unique_case_ids(self) -> "BatchReplayCreateRequest":
        if len(set(self.case_ids)) != len(self.case_ids):
            raise ValueError("批量回放案例不能重复。")
        return self


class BatchReplayItem(ApiModel):
    sequence: int = Field(ge=0)
    case_id: str
    model_kind: ModelKind
    state: BatchReplayItemState
    result_summary: dict[str, object] | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class BatchReplayTaskSummary(ApiModel):
    task_id: str
    client_request_id: str
    state: BatchReplayTaskState
    total_count: int = Field(gt=0)
    completed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    recovery_count: int = Field(ge=0)
    current_case_id: str | None
    error_message: str | None
    progress: float = Field(ge=0, le=1)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class BatchReplayTaskResponse(BatchReplayTaskSummary):
    items: tuple[BatchReplayItem, ...]


class BatchReplayTaskListResponse(ApiModel):
    items: tuple[BatchReplayTaskSummary, ...]
    total: int = Field(ge=0)
