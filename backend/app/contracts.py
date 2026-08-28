from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from math import isclose
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
GitCommitHex = Annotated[
    str,
    StringConstraints(pattern=r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"),
]
Probability = Annotated[float, Field(ge=0, le=1)]
NonNegativeMilliseconds = Annotated[int, Field(ge=0)]


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


class TruthCategory(StrEnum):
    REAL_FREE_LIVING = "REAL_FREE_LIVING"
    REAL_LAB_ACTIVITY = "REAL_LAB_ACTIVITY"
    SIMULATED_FALL = "SIMULATED_FALL"
    SYNTHETIC_ROUTINE = "SYNTHETIC_ROUTINE"
    DERIVED_PERTURBATION = "DERIVED_PERTURBATION"


class ModelKind(StrEnum):
    FALL_DETECTION = "FALL_DETECTION"
    ROUTINE_ANOMALY = "ROUTINE_ANOMALY"
    ACTIVITY_RECOGNITION = "ACTIVITY_RECOGNITION"


class AgeGroup(StrEnum):
    YOUNG_ADULT = "YOUNG_ADULT"
    OLDER_ADULT = "OLDER_ADULT"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class SourceLicenseStatus(StrEnum):
    VERIFIED_OPEN = "VERIFIED_OPEN"
    LOCAL_RESEARCH_ONLY = "LOCAL_RESEARCH_ONLY"
    APPLICATION_REQUIRED = "APPLICATION_REQUIRED"
    UNVERIFIED = "UNVERIFIED"


class SensorKind(StrEnum):
    ACCELEROMETER = "ACCELEROMETER"
    GYROSCOPE = "GYROSCOPE"
    IMU_6AXIS = "IMU_6AXIS"


class StorageFormat(StrEnum):
    CSV = "CSV"
    NPY = "NPY"
    NPZ = "NPZ"


class SourceFileRole(StrEnum):
    ACCELEROMETER = "ACCELEROMETER"
    GYROSCOPE = "GYROSCOPE"
    ANNOTATION = "ANNOTATION"


class GroundTruthEventType(StrEnum):
    ACTIVITY_INTERVAL = "ACTIVITY_INTERVAL"
    FALL_INTERVAL = "FALL_INTERVAL"


class ReplayState(StrEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RESET = "RESET"


class ReplayEventType(StrEnum):
    STATE_CHANGED = "replay.state_changed"
    SENSOR_WINDOW = "sensor.window"
    MODEL_OUTPUT = "model.output"
    ALERT_CANDIDATE = "alert.candidate"
    ERROR = "replay.error"


class ManifestFormat(StrEnum):
    ONNX = "ONNX"
    STATISTICAL_RULES = "STATISTICAL_RULES"


class ApprovalStatus(StrEnum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    EXTERNAL_VALIDATION_REQUIRED = "EXTERNAL_VALIDATION_REQUIRED"
    APPROVED = "APPROVED"


class ChannelDefinition(ContractModel):
    name: NonEmptyText
    quantity: Literal["acceleration", "angular_velocity"]
    unit: Literal["m/s^2", "rad/s"]


class TensorInputContract(ContractModel):
    sample_rate_hz: float = Field(gt=0)
    window_seconds: float = Field(gt=0)
    sample_count: int = Field(gt=0)
    channels: tuple[ChannelDefinition, ...] = Field(min_length=1)
    input_shape: tuple[int | None, ...]

    @model_validator(mode="after")
    def validate_dimensions(self) -> "TensorInputContract":
        expected_samples = self.sample_rate_hz * self.window_seconds
        if not isclose(expected_samples, self.sample_count, abs_tol=1e-6):
            raise ValueError("采样率、窗口时长与样本数不一致。")
        expected_shape = (None, self.sample_count, len(self.channels))
        if self.input_shape != expected_shape:
            raise ValueError(f"输入形状必须为 {expected_shape}。")
        if len({channel.name for channel in self.channels}) != len(self.channels):
            raise ValueError("传感器通道名称不能重复。")
        return self


class RoutineEventInputContract(ContractModel):
    history_days: int = Field(gt=0)
    event_types: tuple[Literal["meal", "nap", "walk"], ...]
    required_fields: tuple[NonEmptyText, ...]


class RoutineEventContract(ContractModel):
    event_id: NonEmptyText
    profile_id: NonEmptyText
    event_type: Literal["meal", "nap", "walk"]
    slot_key: NonEmptyText
    started_at: datetime
    duration_minutes: float = Field(gt=0)
    truth_category: Literal[TruthCategory.SYNTHETIC_ROUTINE] = (
        TruthCategory.SYNTHETIC_ROUTINE
    )


class LabelDefinition(ContractModel):
    code: NonEmptyText
    label_zh_cn: NonEmptyText
    meaning: NonEmptyText


class ModelContract(ContractModel):
    model_kind: ModelKind
    name_zh_cn: NonEmptyText
    task: NonEmptyText
    tensor_input: TensorInputContract | None = None
    routine_event_input: RoutineEventInputContract | None = None
    output_labels: tuple[LabelDefinition, ...] = Field(min_length=1)
    safety_boundary: NonEmptyText

    @model_validator(mode="after")
    def validate_input_variant(self) -> "ModelContract":
        defined_inputs = sum(
            value is not None
            for value in (self.tensor_input, self.routine_event_input)
        )
        if defined_inputs != 1:
            raise ValueError("每个模型必须且只能定义一种输入合同。")
        return self


def model_contracts() -> tuple[ModelContract, ...]:
    acceleration_channels = tuple(
        ChannelDefinition(name=name, quantity="acceleration", unit="m/s^2")
        for name in ("ax", "ay", "az")
    )
    gyroscope_channels = tuple(
        ChannelDefinition(name=name, quantity="angular_velocity", unit="rad/s")
        for name in ("gx", "gy", "gz")
    )
    return (
        ModelContract(
            model_kind=ModelKind.FALL_DETECTION,
            name_zh_cn="腕部跌倒检测",
            task="识别刚刚发生的受控模拟跌倒候选事件",
            tensor_input=TensorInputContract(
                sample_rate_hz=50,
                window_seconds=4,
                sample_count=200,
                channels=acceleration_channels + gyroscope_channels,
                input_shape=(None, 200, 6),
            ),
            output_labels=(
                LabelDefinition(
                    code="adl",
                    label_zh_cn="日常活动",
                    meaning="当前窗口更接近日常活动。",
                ),
                LabelDefinition(
                    code="fall",
                    label_zh_cn="跌倒候选",
                    meaning="当前窗口需要进入事件状态机复核，不能直接宣布真实跌倒。",
                ),
            ),
            safety_boundary=(
                "不预测未来跌倒；单窗口概率不得直接触发真实救援结论。"
            ),
        ),
        ModelContract(
            model_kind=ModelKind.ROUTINE_ANOMALY,
            name_zh_cn="个人规律异常",
            task="判断用餐、午睡和散步是否偏离个人长期规律",
            routine_event_input=RoutineEventInputContract(
                history_days=100,
                event_types=("meal", "nap", "walk"),
                required_fields=(
                    "event_id",
                    "event_type",
                    "started_at",
                    "duration_minutes",
                    "truth_category",
                ),
            ),
            output_labels=(
                LabelDefinition(
                    code="within_routine",
                    label_zh_cn="符合规律",
                    meaning="在当前合成规律合同的正常区间内。",
                ),
                LabelDefinition(
                    code="routine_deviation",
                    label_zh_cn="规律偏离",
                    meaning="时间、次数、时长或缺失至少一项偏离当前规则。",
                ),
            ),
            safety_boundary=(
                "首版只基于 100 天合成生活事件，不得描述为真实老人训练结果。"
            ),
        ),
        ModelContract(
            model_kind=ModelKind.ACTIVITY_RECOGNITION,
            name_zh_cn="腕部活动识别",
            task="把腕部加速度转换为生活事件候选",
            tensor_input=TensorInputContract(
                sample_rate_hz=20,
                window_seconds=20,
                sample_count=400,
                channels=acceleration_channels,
                input_shape=(None, 400, 3),
            ),
            output_labels=(
                LabelDefinition(
                    code="walking",
                    label_zh_cn="走路",
                    meaning="当前窗口的活动候选为走路。",
                ),
                LabelDefinition(
                    code="eating_candidate",
                    label_zh_cn="进食候选",
                    meaning="当前腕部动作可能与进食有关，仍需上下文确认。",
                ),
                LabelDefinition(
                    code="sleep_or_lying_candidate",
                    label_zh_cn="睡眠或躺卧候选",
                    meaning="当前窗口可能是睡眠或躺卧，不能仅凭腕部动作确认睡眠。",
                ),
                LabelDefinition(
                    code="other_unknown",
                    label_zh_cn="其他或未知",
                    meaning="当前模型不能可靠归入前三类。",
                ),
            ),
            safety_boundary=(
                "输出是活动候选，不是生活规律异常，也不是医学风险评分。"
            ),
        ),
    )


class SourceReference(ContractModel):
    source_id: NonEmptyText
    dataset_name: NonEmptyText
    source_url: AnyUrl
    fixed_version: NonEmptyText
    license_status: SourceLicenseStatus
    license_reference: NonEmptyText
    redistribution_allowed: bool | None
    verified_at: datetime
    notes: NonEmptyText


class CaseContract(ContractModel):
    case_id: NonEmptyText
    title: NonEmptyText
    description: str = ""
    truth_category: TruthCategory
    source: SourceReference
    source_record_path: NonEmptyText
    source_sha256: Sha256Hex
    participant_id: NonEmptyText | None = None
    age_group: AgeGroup
    device_name: NonEmptyText
    wear_position: NonEmptyText
    original_sample_rate_hz: float | None = Field(default=None, gt=0)
    activity_label: NonEmptyText | None = None
    has_accelerometer: bool
    has_gyroscope: bool
    allowed_models: tuple[ModelKind, ...]
    derivation_parent_case_id: NonEmptyText | None = None
    processing_command: NonEmptyText
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_model_eligibility(self) -> "CaseContract":
        if not _is_safe_relative_path(self.source_record_path):
            raise ValueError("来源记录路径必须是仓库内安全相对路径。")
        if len(set(self.allowed_models)) != len(self.allowed_models):
            raise ValueError("allowed_models 不能包含重复模型。")
        if ModelKind.FALL_DETECTION in self.allowed_models:
            if not self.has_accelerometer or not self.has_gyroscope:
                raise ValueError("六轴跌倒模型只接受真实存在的加速度和陀螺仪通道。")
        if (
            self.truth_category is TruthCategory.DERIVED_PERTURBATION
            and self.derivation_parent_case_id is None
        ):
            raise ValueError("派生扰动案例必须记录父案例。")
        if (
            self.truth_category is not TruthCategory.DERIVED_PERTURBATION
            and self.derivation_parent_case_id is not None
        ):
            raise ValueError("非派生案例不能伪装成派生关系。")
        return self


class RoutineProfileContract(ContractModel):
    profile_id: NonEmptyText
    case: CaseContract
    history_days: Literal[100] = 100
    history_start: date
    history_end: date
    seed: int
    event_count: int = Field(gt=0)
    events_relative_path: NonEmptyText
    events_sha256: Sha256Hex
    created_at: datetime

    @model_validator(mode="after")
    def validate_profile(self) -> "RoutineProfileContract":
        if self.case.case_id != self.profile_id:
            raise ValueError("规律档案与案例标识必须一致。")
        if self.case.truth_category is not TruthCategory.SYNTHETIC_ROUTINE:
            raise ValueError("规律档案案例必须标记为 SYNTHETIC_ROUTINE。")
        if self.case.allowed_models != (ModelKind.ROUTINE_ANOMALY,):
            raise ValueError("合成规律案例只能进入 ROUTINE_ANOMALY。")
        if self.case.has_accelerometer or self.case.has_gyroscope:
            raise ValueError("合成规律案例不能伪装成传感器记录。")
        if (self.history_end - self.history_start).days + 1 != self.history_days:
            raise ValueError("规律档案日期范围必须恰好覆盖 100 天。")
        if not _is_safe_relative_path(self.events_relative_path):
            raise ValueError("规律事件文件路径必须是仓库内安全相对路径。")
        return self


class SensorWindow(ContractModel):
    window_id: NonEmptyText
    case_id: NonEmptyText
    stream_id: NonEmptyText
    sensor_kind: SensorKind
    sequence: int = Field(ge=0)
    start_offset_ms: NonNegativeMilliseconds
    sample_rate_hz: float = Field(gt=0)
    channels: tuple[NonEmptyText, ...] = Field(min_length=1)
    units: tuple[NonEmptyText, ...] = Field(min_length=1)
    samples: tuple[tuple[float, ...], ...] = Field(min_length=1)
    source_sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_sample_matrix(self) -> "SensorWindow":
        if len(self.channels) != len(self.units):
            raise ValueError("通道和单位数量必须一致。")
        if any(len(row) != len(self.channels) for row in self.samples):
            raise ValueError("每个采样点的列数必须与通道数量一致。")
        if self.sensor_kind is SensorKind.IMU_6AXIS and tuple(self.channels) != (
            "ax",
            "ay",
            "az",
            "gx",
            "gy",
            "gz",
        ):
            raise ValueError("六轴 IMU 通道顺序必须为 ax, ay, az, gx, gy, gz。")
        if self.sensor_kind is SensorKind.IMU_6AXIS and tuple(self.units) != (
            "m/s^2",
            "m/s^2",
            "m/s^2",
            "rad/s",
            "rad/s",
            "rad/s",
        ):
            raise ValueError("六轴 IMU 单位必须为三轴 m/s^2 和三轴 rad/s。")
        return self


class SensorStreamContract(ContractModel):
    stream_id: NonEmptyText
    case_id: NonEmptyText
    sensor_kind: SensorKind
    sample_rate_hz: float = Field(gt=0)
    channels: tuple[NonEmptyText, ...] = Field(min_length=1)
    units: tuple[NonEmptyText, ...] = Field(min_length=1)
    sample_count: int = Field(gt=0)
    duration_ms: int = Field(gt=0)
    storage_format: StorageFormat
    relative_path: NonEmptyText
    content_sha256: Sha256Hex
    created_at: datetime

    @model_validator(mode="after")
    def validate_stream_contract(self) -> "SensorStreamContract":
        if not _is_safe_relative_path(self.relative_path):
            raise ValueError("传感器文件路径必须是仓库内安全相对路径。")
        if len(self.channels) != len(self.units):
            raise ValueError("通道和单位数量必须一致。")
        if self.sensor_kind is SensorKind.IMU_6AXIS:
            if tuple(self.channels) != ("ax", "ay", "az", "gx", "gy", "gz"):
                raise ValueError("六轴 IMU 通道顺序必须为 ax, ay, az, gx, gy, gz。")
            if tuple(self.units) != (
                "m/s^2",
                "m/s^2",
                "m/s^2",
                "rad/s",
                "rad/s",
                "rad/s",
            ):
                raise ValueError("六轴 IMU 单位必须为三轴 m/s^2 和三轴 rad/s。")
        return self


class SensorQualityContract(ContractModel):
    stream_id: NonEmptyText
    accel_rows: int = Field(gt=1)
    accel_unique_timestamps: int = Field(gt=1)
    gyro_rows: int = Field(gt=1)
    gyro_unique_timestamps: int = Field(gt=1)
    accel_effective_rate_hz: float = Field(gt=0)
    gyro_effective_rate_hz: float = Field(gt=0)
    accel_median_dt_ms: float = Field(gt=0)
    gyro_median_dt_ms: float = Field(gt=0)
    accel_max_gap_ms: float = Field(gt=0)
    gyro_max_gap_ms: float = Field(gt=0)
    flags: tuple[NonEmptyText, ...]


class CaseSourceFile(ContractModel):
    file_id: NonEmptyText
    case_id: NonEmptyText
    role: SourceFileRole
    source_relative_path: NonEmptyText
    source_sha256: Sha256Hex

    @model_validator(mode="after")
    def validate_source_path(self) -> "CaseSourceFile":
        if not _is_safe_relative_path(self.source_relative_path):
            raise ValueError("原始来源文件路径必须是来源仓库内安全相对路径。")
        return self


class GroundTruthEvent(ContractModel):
    event_id: NonEmptyText
    case_id: NonEmptyText
    event_type: GroundTruthEventType
    label: NonEmptyText
    start_offset_ms: NonNegativeMilliseconds
    end_offset_ms: NonNegativeMilliseconds
    truth_category: TruthCategory
    annotation_source_sha256: Sha256Hex
    notes: NonEmptyText

    @model_validator(mode="after")
    def validate_event_bounds(self) -> "GroundTruthEvent":
        if self.end_offset_ms <= self.start_offset_ms:
            raise ValueError("真实标签事件结束位置必须晚于开始位置。")
        if (
            self.event_type is GroundTruthEventType.FALL_INTERVAL
            and self.truth_category is not TruthCategory.SIMULATED_FALL
        ):
            raise ValueError("受控跌倒区间必须标记为 SIMULATED_FALL。")
        return self


class SelectionRule(ContractModel):
    age_group: AgeGroup
    truth_category: TruthCategory
    count: int = Field(gt=0)


class SelectionPolicy(ContractModel):
    policy_id: NonEmptyText
    total_count: int = Field(gt=0)
    rules: tuple[SelectionRule, ...] = Field(min_length=1)
    ordering: NonEmptyText

    @model_validator(mode="after")
    def validate_total(self) -> "SelectionPolicy":
        if sum(rule.count for rule in self.rules) != self.total_count:
            raise ValueError("分层选择规则数量之和必须等于总案例数。")
        return self


class ImportRunContract(ContractModel):
    run_id: NonEmptyText
    source_id: NonEmptyText
    importer_version: NonEmptyText
    source_commit: GitCommitHex
    processing_source_commit: GitCommitHex
    selection_policy: SelectionPolicy
    catalog_relative_path: NonEmptyText
    catalog_sha256: Sha256Hex
    created_at: datetime

    @model_validator(mode="after")
    def validate_catalog_path(self) -> "ImportRunContract":
        if not _is_safe_relative_path(self.catalog_relative_path):
            raise ValueError("案例目录路径必须是仓库内安全相对路径。")
        return self


class InferenceContext(ContractModel):
    output_id: NonEmptyText
    case_id: NonEmptyText
    session_id: NonEmptyText
    model_id: NonEmptyText
    model_version: NonEmptyText
    input_window_id: NonEmptyText
    start_offset_ms: NonNegativeMilliseconds
    end_offset_ms: NonNegativeMilliseconds
    created_at: datetime

    @model_validator(mode="after")
    def validate_window_bounds(self) -> "InferenceContext":
        if self.end_offset_ms <= self.start_offset_ms:
            raise ValueError("推理窗口结束位置必须晚于开始位置。")
        return self


class BinaryProbabilities(ContractModel):
    adl: Probability
    fall: Probability

    @model_validator(mode="after")
    def validate_probability_sum(self) -> "BinaryProbabilities":
        if not isclose(self.adl + self.fall, 1.0, abs_tol=1e-4):
            raise ValueError("跌倒检测概率之和必须为 1。")
        return self


class FallModelOutput(ContractModel):
    model_kind: Literal[ModelKind.FALL_DETECTION] = ModelKind.FALL_DETECTION
    context: InferenceContext
    probabilities: BinaryProbabilities
    threshold: Probability
    window_above_threshold: bool
    event_state: Literal[
        "NO_CANDIDATE", "CANDIDATE_STARTED", "CANDIDATE_ACTIVE", "CANDIDATE_ENDED"
    ]
    deployment_approved: bool
    explanation: NonEmptyText

    @model_validator(mode="after")
    def validate_threshold_decision(self) -> "FallModelOutput":
        if self.window_above_threshold != (self.probabilities.fall >= self.threshold):
            raise ValueError("窗口阈值判断必须与保存的概率和阈值一致。")
        return self


class RoutineAssessment(ContractModel):
    event_type: Literal["meal", "nap", "walk"]
    status: Literal[
        "WITHIN_ROUTINE",
        "EARLY",
        "LATE",
        "MISSING",
        "COUNT_DEVIATION",
        "DURATION_DEVIATION",
    ]
    anomaly_score: Probability | None = None
    evidence: tuple[NonEmptyText, ...] = Field(min_length=1)


class RoutineModelOutput(ContractModel):
    model_kind: Literal[ModelKind.ROUTINE_ANOMALY] = ModelKind.ROUTINE_ANOMALY
    context: InferenceContext
    assessments: tuple[RoutineAssessment, ...] = Field(min_length=1)
    truth_category: Literal[TruthCategory.SYNTHETIC_ROUTINE]
    explanation: NonEmptyText


class ActivityProbabilities(ContractModel):
    walking: Probability
    eating_candidate: Probability
    sleep_or_lying_candidate: Probability
    other_unknown: Probability

    @model_validator(mode="after")
    def validate_probability_sum(self) -> "ActivityProbabilities":
        total = sum(
            (
                self.walking,
                self.eating_candidate,
                self.sleep_or_lying_candidate,
                self.other_unknown,
            )
        )
        if not isclose(total, 1.0, abs_tol=1e-4):
            raise ValueError("活动识别概率之和必须为 1。")
        return self


class ActivityModelOutput(ContractModel):
    model_kind: Literal[ModelKind.ACTIVITY_RECOGNITION] = (
        ModelKind.ACTIVITY_RECOGNITION
    )
    context: InferenceContext
    probabilities: ActivityProbabilities
    predicted_label: Literal[
        "walking", "eating_candidate", "sleep_or_lying_candidate", "other_unknown"
    ]
    explanation: NonEmptyText

    @model_validator(mode="after")
    def validate_predicted_label(self) -> "ActivityModelOutput":
        scores = self.probabilities.model_dump()
        if scores[self.predicted_label] != max(scores.values()):
            raise ValueError("活动标签必须对应最高保存概率；并列时可任选并列标签。")
        return self


ModelOutput = Annotated[
    FallModelOutput | RoutineModelOutput | ActivityModelOutput,
    Field(discriminator="model_kind"),
]


class ModelManifest(ContractModel):
    manifest_id: NonEmptyText
    model_id: NonEmptyText
    model_kind: ModelKind
    version: NonEmptyText
    format: ManifestFormat
    source_commit: GitCommitHex
    artifact_relative_path: NonEmptyText | None = None
    artifact_sha256: Sha256Hex | None = None
    contract: ModelContract
    training_truth_categories: tuple[TruthCategory, ...]
    training_data_references: tuple[NonEmptyText, ...] = Field(min_length=1)
    evaluation_reference: NonEmptyText
    limitations: tuple[NonEmptyText, ...] = Field(min_length=1)
    deployment_approved: bool
    approval_status: ApprovalStatus
    external_validation_completed: bool
    created_at: datetime

    @model_validator(mode="after")
    def validate_approval_and_artifact(self) -> "ModelManifest":
        if self.contract.model_kind is not self.model_kind:
            raise ValueError("manifest 的模型类型必须与输入输出合同一致。")
        if (self.artifact_relative_path is None) != (self.artifact_sha256 is None):
            raise ValueError("模型文件路径和 SHA-256 必须同时提供或同时为空。")
        if self.artifact_relative_path is not None and not _is_safe_relative_path(
            self.artifact_relative_path
        ):
            raise ValueError("模型文件路径必须是仓库内安全相对路径。")
        if self.deployment_approved:
            if self.approval_status is not ApprovalStatus.APPROVED:
                raise ValueError("通过部署审批的模型必须标记 APPROVED。")
            if not self.external_validation_completed:
                raise ValueError("没有完成外部验证的模型不能通过部署审批。")
        elif self.approval_status is ApprovalStatus.APPROVED:
            raise ValueError("未通过部署审批的模型不能标记 APPROVED。")
        return self


class ReplayStateChangedEvent(ContractModel):
    event: Literal[ReplayEventType.STATE_CHANGED] = ReplayEventType.STATE_CHANGED
    event_id: NonEmptyText
    session_id: NonEmptyText
    sequence: int = Field(ge=0)
    offset_ms: NonNegativeMilliseconds
    emitted_at: datetime
    state: ReplayState
    message: NonEmptyText


class SensorWindowEvent(ContractModel):
    event: Literal[ReplayEventType.SENSOR_WINDOW] = ReplayEventType.SENSOR_WINDOW
    event_id: NonEmptyText
    session_id: NonEmptyText
    sequence: int = Field(ge=0)
    offset_ms: NonNegativeMilliseconds
    emitted_at: datetime
    window: SensorWindow


class ModelOutputEvent(ContractModel):
    event: Literal[ReplayEventType.MODEL_OUTPUT] = ReplayEventType.MODEL_OUTPUT
    event_id: NonEmptyText
    session_id: NonEmptyText
    sequence: int = Field(ge=0)
    offset_ms: NonNegativeMilliseconds
    emitted_at: datetime
    output: ModelOutput


class AlertCandidateEvent(ContractModel):
    event: Literal[ReplayEventType.ALERT_CANDIDATE] = ReplayEventType.ALERT_CANDIDATE
    event_id: NonEmptyText
    session_id: NonEmptyText
    sequence: int = Field(ge=0)
    offset_ms: NonNegativeMilliseconds
    emitted_at: datetime
    source_output_id: NonEmptyText
    candidate_type: Literal["FALL_CANDIDATE", "ROUTINE_DEVIATION"]
    requires_human_review: Literal[True] = True
    explanation: NonEmptyText


class ReplayErrorEvent(ContractModel):
    event: Literal[ReplayEventType.ERROR] = ReplayEventType.ERROR
    event_id: NonEmptyText
    session_id: NonEmptyText
    sequence: int = Field(ge=0)
    offset_ms: NonNegativeMilliseconds
    emitted_at: datetime
    code: NonEmptyText
    message: NonEmptyText
    retryable: bool


ReplayEvent = Annotated[
    ReplayStateChangedEvent
    | SensorWindowEvent
    | ModelOutputEvent
    | AlertCandidateEvent
    | ReplayErrorEvent,
    Field(discriminator="event"),
]


class ContractCatalog(ContractModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    database_schema_version: int = 4
    truth_categories: tuple[TruthCategory, ...]
    model_contracts: tuple[ModelContract, ...]
    replay_event_types: tuple[ReplayEventType, ...]
    invariants: tuple[NonEmptyText, ...]


def contract_catalog() -> ContractCatalog:
    return ContractCatalog(
        truth_categories=tuple(TruthCategory),
        model_contracts=model_contracts(),
        replay_event_types=tuple(ReplayEventType),
        invariants=(
            "三个模型独立输出，不生成未经校准的综合医学风险分数。",
            "缺少真实陀螺仪通道的案例不得进入六轴跌倒模型。",
            "年轻参与者的受控模拟跌倒必须标记为 SIMULATED_FALL。",
            "老人参与者的 WEDA-FALL 数据只用于日常活动误报分析。",
            "没有完成外部验证的模型必须保持 deployment_approved=false。",
            "所有指标只能来自保存了配置、分组和命令的实际运行。",
        ),
    )
