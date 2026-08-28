from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from backend.app.contracts import (
    ActivityModelOutput,
    ActivityProbabilities,
    AgeGroup,
    ApprovalStatus,
    CaseContract,
    FallModelOutput,
    InferenceContext,
    ManifestFormat,
    ModelKind,
    ModelManifest,
    SensorKind,
    SensorWindow,
    SourceLicenseStatus,
    SourceReference,
    TruthCategory,
    contract_catalog,
    model_contracts,
)


NOW = datetime(2026, 8, 28, 8, 0, tzinfo=UTC)
SHA256 = "a" * 64
GIT_COMMIT = "b" * 40


def source_reference() -> SourceReference:
    return SourceReference(
        source_id="test-source",
        dataset_name="合同测试来源",
        source_url="https://example.test/dataset",
        fixed_version=GIT_COMMIT,
        license_status=SourceLicenseStatus.UNVERIFIED,
        license_reference="测试数据不用于实际发布",
        redistribution_allowed=None,
        verified_at=NOW,
        notes="只用于验证合同，不代表真实参与者或真实指标。",
    )


def inference_context() -> InferenceContext:
    return InferenceContext(
        output_id="output-001",
        case_id="case-001",
        session_id="session-001",
        model_id="model-001",
        model_version="0.0-test",
        input_window_id="window-001",
        start_offset_ms=0,
        end_offset_ms=4000,
        created_at=NOW,
    )


def test_model_contracts_lock_three_independent_inputs() -> None:
    contracts = {contract.model_kind: contract for contract in model_contracts()}

    assert set(contracts) == set(ModelKind)
    fall = contracts[ModelKind.FALL_DETECTION].tensor_input
    assert fall is not None
    assert fall.sample_rate_hz == 50
    assert fall.window_seconds == 4
    assert fall.sample_count == 200
    assert fall.input_shape == (None, 200, 6)
    assert tuple(channel.name for channel in fall.channels) == (
        "ax",
        "ay",
        "az",
        "gx",
        "gy",
        "gz",
    )

    routine = contracts[ModelKind.ROUTINE_ANOMALY].routine_event_input
    assert routine is not None
    assert routine.history_days == 100
    assert routine.event_types == ("meal", "nap", "walk")

    activity = contracts[ModelKind.ACTIVITY_RECOGNITION].tensor_input
    assert activity is not None
    assert activity.sample_rate_hz == 20
    assert activity.window_seconds == 20
    assert activity.sample_count == 400
    assert activity.input_shape == (None, 400, 3)


def test_case_contract_rejects_missing_real_gyroscope_for_fall_model() -> None:
    with pytest.raises(ValidationError, match="真实存在的加速度和陀螺仪"):
        CaseContract(
            case_id="case-001",
            title="没有陀螺仪的合同测试案例",
            truth_category=TruthCategory.REAL_LAB_ACTIVITY,
            source=source_reference(),
            source_record_path="test/accel.csv",
            source_sha256=SHA256,
            age_group=AgeGroup.UNKNOWN,
            device_name="测试设备",
            wear_position="wrist",
            original_sample_rate_hz=50,
            activity_label="walking",
            has_accelerometer=True,
            has_gyroscope=False,
            allowed_models=(ModelKind.FALL_DETECTION,),
            processing_command="pytest contract validation",
            created_at=NOW,
            updated_at=NOW,
        )


def test_case_contract_rejects_source_path_escape() -> None:
    with pytest.raises(ValidationError, match="安全相对路径"):
        CaseContract(
            case_id="case-escape",
            title="路径逃逸测试",
            truth_category=TruthCategory.REAL_LAB_ACTIVITY,
            source=source_reference(),
            source_record_path="../outside.csv",
            source_sha256=SHA256,
            age_group=AgeGroup.UNKNOWN,
            device_name="测试设备",
            wear_position="wrist",
            original_sample_rate_hz=20,
            activity_label="walking",
            has_accelerometer=True,
            has_gyroscope=False,
            allowed_models=(ModelKind.ACTIVITY_RECOGNITION,),
            processing_command="pytest contract validation",
            created_at=NOW,
            updated_at=NOW,
        )


def test_derived_case_requires_parent_case() -> None:
    with pytest.raises(ValidationError, match="必须记录父案例"):
        CaseContract(
            case_id="derived-001",
            title="缺少父案例的派生扰动",
            truth_category=TruthCategory.DERIVED_PERTURBATION,
            source=source_reference(),
            source_record_path="test/derived.csv",
            source_sha256=SHA256,
            age_group=AgeGroup.NOT_APPLICABLE,
            device_name="测试设备",
            wear_position="wrist",
            has_accelerometer=True,
            has_gyroscope=False,
            allowed_models=(ModelKind.ACTIVITY_RECOGNITION,),
            processing_command="pytest contract validation",
            created_at=NOW,
            updated_at=NOW,
        )


def test_sensor_window_rejects_fake_six_axis_shape() -> None:
    with pytest.raises(ValidationError, match="六轴 IMU 通道顺序"):
        SensorWindow(
            window_id="window-001",
            case_id="case-001",
            stream_id="stream-001",
            sensor_kind=SensorKind.IMU_6AXIS,
            sequence=0,
            start_offset_ms=0,
            sample_rate_hz=50,
            channels=("ax", "ay", "az"),
            units=("m/s^2", "m/s^2", "m/s^2"),
            samples=((0.0, 0.0, 9.8),),
            source_sha256=SHA256,
        )


def test_model_outputs_preserve_saved_decision_logic() -> None:
    with pytest.raises(ValidationError, match="阈值判断"):
        FallModelOutput(
            context=inference_context(),
            probabilities={"adl": 0.2, "fall": 0.8},
            threshold=0.7,
            window_above_threshold=False,
            event_state="NO_CANDIDATE",
            deployment_approved=False,
            explanation="测试输出，不代表真实模型指标。",
        )

    with pytest.raises(ValidationError, match="最高保存概率"):
        ActivityModelOutput(
            context=inference_context(),
            probabilities=ActivityProbabilities(
                walking=0.7,
                eating_candidate=0.1,
                sleep_or_lying_candidate=0.1,
                other_unknown=0.1,
            ),
            predicted_label="other_unknown",
            explanation="测试输出，不代表真实模型指标。",
        )


def test_manifest_cannot_approve_model_without_external_validation() -> None:
    fall_contract = next(
        contract
        for contract in model_contracts()
        if contract.model_kind is ModelKind.FALL_DETECTION
    )
    with pytest.raises(ValidationError, match="外部验证"):
        ModelManifest(
            manifest_id="manifest-001",
            model_id="fall-test",
            model_kind=ModelKind.FALL_DETECTION,
            version="0.0-test",
            format=ManifestFormat.ONNX,
            source_commit=GIT_COMMIT,
            artifact_relative_path="models/test.onnx",
            artifact_sha256=SHA256,
            contract=fall_contract,
            training_truth_categories=(TruthCategory.SIMULATED_FALL,),
            training_data_references=("test-only",),
            evaluation_reference="test-only",
            limitations=("测试 manifest，不可用于部署。",),
            deployment_approved=True,
            approval_status=ApprovalStatus.APPROVED,
            external_validation_completed=False,
            created_at=NOW,
        )


def test_manifest_rejects_artifact_outside_repository() -> None:
    activity_contract = next(
        contract
        for contract in model_contracts()
        if contract.model_kind is ModelKind.ACTIVITY_RECOGNITION
    )
    with pytest.raises(ValidationError, match="安全相对路径"):
        ModelManifest(
            manifest_id="manifest-escape",
            model_id="activity-test",
            model_kind=ModelKind.ACTIVITY_RECOGNITION,
            version="0.0-test",
            format=ManifestFormat.ONNX,
            source_commit=GIT_COMMIT,
            artifact_relative_path="C:\\outside\\model.onnx",
            artifact_sha256=SHA256,
            contract=activity_contract,
            training_truth_categories=(TruthCategory.REAL_LAB_ACTIVITY,),
            training_data_references=("test-only",),
            evaluation_reference="test-only",
            limitations=("测试 manifest，不可用于部署。",),
            deployment_approved=False,
            approval_status=ApprovalStatus.RESEARCH_ONLY,
            external_validation_completed=False,
            created_at=NOW,
        )


def test_contract_catalog_has_no_combined_health_risk() -> None:
    catalog = contract_catalog()

    assert catalog.contract_version == "1.0.0"
    assert catalog.database_schema_version == 3
    assert len(catalog.model_contracts) == 3
    assert any("独立输出" in invariant for invariant in catalog.invariants)
    assert "combined" not in catalog.model_dump_json().lower()
