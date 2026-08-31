from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from math import isfinite
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
PseudonymousId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$"),
]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _is_safe_relative_path(value: str) -> bool:
    windows_path = PureWindowsPath(value)
    posix_path = PurePosixPath(value)
    return not (
        windows_path.is_absolute()
        or windows_path.drive
        or posix_path.is_absolute()
        or ".." in windows_path.parts
        or ".." in posix_path.parts
    )


class StorageLayer(StrEnum):
    RAW_IMMUTABLE = "RAW_IMMUTABLE"
    NORMALIZED_DERIVED = "NORMALIZED_DERIVED"


class SensorProfileKind(StrEnum):
    ACCELEROMETER_3AXIS = "ACCELEROMETER_3AXIS"
    IMU_6AXIS = "IMU_6AXIS"


class WearSide(StrEnum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class EventType(StrEnum):
    ACCIDENTAL_FALL = "ACCIDENTAL_FALL"
    NEAR_FALL = "NEAR_FALL"
    INSTABILITY = "INSTABILITY"
    TRIP_RECOVERY = "TRIP_RECOVERY"
    RAPID_SIT = "RAPID_SIT"
    INTENTIONAL_LIE_DOWN = "INTENTIONAL_LIE_DOWN"
    ORDINARY_TRANSITION = "ORDINARY_TRANSITION"
    DEVICE_ARTIFACT = "DEVICE_ARTIFACT"


class LabelSourceKind(StrEnum):
    VIDEO_DOUBLE_REVIEW = "VIDEO_DOUBLE_REVIEW"
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    PARTICIPANT_REPORT = "PARTICIPANT_REPORT"
    CAREGIVER_REPORT = "CAREGIVER_REPORT"
    CLINICAL_RECORD = "CLINICAL_RECORD"
    ENGINEERING_FIXTURE = "ENGINEERING_FIXTURE"


class LabelConfidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ChannelSpec(ContractModel):
    name: NonEmptyText
    quantity: Literal["acceleration", "angular_velocity"]
    unit: Literal["m/s^2", "rad/s"]

    @model_validator(mode="after")
    def validate_unit(self) -> "ChannelSpec":
        expected = {
            "acceleration": "m/s^2",
            "angular_velocity": "rad/s",
        }[self.quantity]
        if self.unit != expected:
            raise ValueError(f"{self.quantity} 必须使用 {expected}。")
        return self


class SensorProfile(ContractModel):
    profile_id: NonEmptyText
    profile_kind: SensorProfileKind
    device_model: NonEmptyText
    nominal_sample_rate_hz: float = Field(gt=0)
    channels: tuple[ChannelSpec, ...] = Field(min_length=1)
    wear_side: WearSide
    timezone_name: NonEmptyText
    calibration_version: NonEmptyText

    @model_validator(mode="after")
    def validate_profile_shape(self) -> "SensorProfile":
        names = tuple(channel.name for channel in self.channels)
        if len(set(names)) != len(names):
            raise ValueError("传感器通道不能重复。")
        if self.profile_kind is SensorProfileKind.ACCELEROMETER_3AXIS:
            expected_names = ("ax", "ay", "az")
            expected_quantities = ("acceleration",) * 3
        else:
            expected_names = ("ax", "ay", "az", "gx", "gy", "gz")
            expected_quantities = ("acceleration",) * 3 + ("angular_velocity",) * 3
        if names != expected_names:
            raise ValueError(f"{self.profile_kind} 通道顺序必须为 {expected_names}。")
        if tuple(channel.quantity for channel in self.channels) != expected_quantities:
            raise ValueError("通道物理量与传感器配置不一致。")
        return self


class SensorSample(ContractModel):
    sequence: int = Field(ge=0)
    utc_timestamp_ns: int = Field(gt=0)
    monotonic_timestamp_ns: int = Field(gt=0)
    values: tuple[float, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_finite_values(self) -> "SensorSample":
        if not all(isfinite(value) for value in self.values):
            raise ValueError("传感器数值必须全部为有限数。")
        return self


class QualityAssessment(ContractModel):
    missing_sample_fraction: float = Field(ge=0, le=1)
    duplicate_timestamp_count: int = Field(ge=0)
    out_of_order_count: int = Field(ge=0)
    synchronization_error_ms: float = Field(ge=0)
    clock_drift_ms: float = Field(ge=0)
    quality_flags: tuple[NonEmptyText, ...]
    accepted_for_second_scale: bool

    @model_validator(mode="after")
    def validate_second_scale_gate(self) -> "QualityAssessment":
        should_accept = (
            self.duplicate_timestamp_count == 0
            and self.out_of_order_count == 0
            and self.synchronization_error_ms <= 100
            and self.clock_drift_ms <= 100
        )
        if self.accepted_for_second_scale != should_accept:
            raise ValueError("数秒级质量 Gate 与时间戳质量字段不一致。")
        return self


class SensorSegment(ContractModel):
    segment_id: PseudonymousId
    storage_layer: StorageLayer
    participant_id: PseudonymousId
    site_id: PseudonymousId
    device_id: PseudonymousId
    session_id: PseudonymousId
    profile: SensorProfile
    started_at: datetime
    source_relative_path: NonEmptyText
    source_sha256: Sha256Hex
    parent_segment_id: PseudonymousId | None = None
    raw_immutable: bool
    withdrawal_locator: PseudonymousId
    quality: QualityAssessment
    samples: tuple[SensorSample, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_segment(self) -> "SensorSegment":
        if not _is_safe_relative_path(self.source_relative_path):
            raise ValueError("传感器段路径必须是安全相对路径。")
        if self.started_at.tzinfo is None or self.started_at.utcoffset() is None:
            raise ValueError("started_at 必须包含可审计时区。")
        if self.storage_layer is StorageLayer.RAW_IMMUTABLE:
            if not self.raw_immutable or self.parent_segment_id is not None:
                raise ValueError("原始层必须不可变且不能声明父派生段。")
        else:
            if self.raw_immutable or self.parent_segment_id is None:
                raise ValueError("规范化派生层必须指向原始父段且不能伪装成原始不可变层。")

        expected_sequences = tuple(range(len(self.samples)))
        if tuple(sample.sequence for sample in self.samples) != expected_sequences:
            raise ValueError("采样序号必须从 0 开始连续且不得重复。")
        utc_timestamps = tuple(sample.utc_timestamp_ns for sample in self.samples)
        monotonic_timestamps = tuple(
            sample.monotonic_timestamp_ns for sample in self.samples
        )
        if any(right <= left for left, right in zip(utc_timestamps, utc_timestamps[1:])):
            raise ValueError("UTC 时间戳必须严格递增，禁止乱序或重复。")
        if any(
            right <= left
            for left, right in zip(monotonic_timestamps, monotonic_timestamps[1:])
        ):
            raise ValueError("单调时间戳必须严格递增，禁止乱序或重复。")
        width = len(self.profile.channels)
        if any(len(sample.values) != width for sample in self.samples):
            raise ValueError("每个采样点必须完整包含配置声明的所有通道。")
        return self


class EventAnnotation(ContractModel):
    event_id: PseudonymousId
    participant_id: PseudonymousId
    site_id: PseudonymousId
    device_id: PseudonymousId
    session_id: PseudonymousId
    event_type: EventType
    t_instability_ns: int = Field(gt=0)
    t_impact_ns: int | None = Field(default=None, gt=0)
    t_recovery_or_assist_ns: int = Field(gt=0)
    label_source: LabelSourceKind
    adjudicator_ids: tuple[PseudonymousId, ...] = Field(min_length=2)
    confidence: LabelConfidence
    synchronization_error_ms: float = Field(ge=0)
    notes: NonEmptyText

    @model_validator(mode="after")
    def validate_event_times_and_adjudication(self) -> "EventAnnotation":
        if len(set(self.adjudicator_ids)) != len(self.adjudicator_ids):
            raise ValueError("双人裁决者必须是不同的去标识化人员。")
        if self.t_impact_ns is not None and self.t_impact_ns < self.t_instability_ns:
            raise ValueError("t_impact 不能早于 t_instability。")
        if self.event_type is EventType.ACCIDENTAL_FALL and self.t_impact_ns is None:
            raise ValueError("真实意外跌倒必须记录 t_impact。")
        latest_event_time = self.t_impact_ns or self.t_instability_ns
        if self.t_recovery_or_assist_ns <= latest_event_time:
            raise ValueError("恢复或协助时刻必须晚于事件锚点。")
        if self.event_type in {EventType.NEAR_FALL, EventType.INSTABILITY}:
            if self.t_impact_ns is not None:
                raise ValueError("近跌倒/失稳不允许伪造撞击锚点。")
        if self.synchronization_error_ms > 100:
            raise ValueError("同步误差超过 100 ms，不能进入数秒级研究合同。")
        return self


class ResearchRecordBundle(ContractModel):
    bundle_id: PseudonymousId
    segments: tuple[SensorSegment, ...] = Field(min_length=1)
    annotations: tuple[EventAnnotation, ...]

    @model_validator(mode="after")
    def validate_identifiers_do_not_mix(self) -> "ResearchRecordBundle":
        if any(
            not segment.quality.accepted_for_second_scale for segment in self.segments
        ):
            raise ValueError("质量或时钟 Gate 未通过的传感器段不能进入数秒级研究包。")
        identities = {
            (
                segment.participant_id,
                segment.site_id,
                segment.device_id,
                segment.session_id,
            )
            for segment in self.segments
        }
        if len(identities) != 1:
            raise ValueError("同一研究包不能混入不同参与者、地点、设备或会话。")
        identity = next(iter(identities))
        for annotation in self.annotations:
            event_identity = (
                annotation.participant_id,
                annotation.site_id,
                annotation.device_id,
                annotation.session_id,
            )
            if event_identity != identity:
                raise ValueError("事件标签与传感器段身份不一致。")
        return self


class WithdrawalIndexEntry(ContractModel):
    withdrawal_locator: PseudonymousId
    participant_id: PseudonymousId
    segment_ids: tuple[PseudonymousId, ...]
    event_ids: tuple[PseudonymousId, ...]
    restricted_mapping_reference: NonEmptyText
    access_scope: Literal["DATA_CONTROLLER_ONLY"] = "DATA_CONTROLLER_ONLY"

    @model_validator(mode="after")
    def validate_restricted_mapping(self) -> "WithdrawalIndexEntry":
        if not _is_safe_relative_path(self.restricted_mapping_reference):
            raise ValueError("撤回映射引用必须是受控区内的安全相对引用。")
        return self
