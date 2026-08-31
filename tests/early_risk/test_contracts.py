from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from research.early_risk.contracts import (
    ChannelSpec,
    EventAnnotation,
    EventType,
    LabelConfidence,
    LabelSourceKind,
    QualityAssessment,
    ResearchRecordBundle,
    SensorProfile,
    SensorProfileKind,
    SensorSample,
    SensorSegment,
    StorageLayer,
    WearSide,
    WithdrawalIndexEntry,
)


SHA256 = "a" * 64


def profile() -> SensorProfile:
    return SensorProfile(
        profile_id="imu-6axis-50hz-v1",
        profile_kind=SensorProfileKind.IMU_6AXIS,
        device_model="fixture-watch",
        nominal_sample_rate_hz=50,
        channels=tuple(
            ChannelSpec(
                name=name,
                quantity="acceleration" if name.startswith("a") else "angular_velocity",
                unit="m/s^2" if name.startswith("a") else "rad/s",
            )
            for name in ("ax", "ay", "az", "gx", "gy", "gz")
        ),
        wear_side=WearSide.LEFT,
        timezone_name="Asia/Shanghai",
        calibration_version="fixture-calibration-v1",
    )


def quality(**updates: object) -> QualityAssessment:
    payload: dict[str, object] = {
        "missing_sample_fraction": 0,
        "duplicate_timestamp_count": 0,
        "out_of_order_count": 0,
        "synchronization_error_ms": 50,
        "clock_drift_ms": 20,
        "quality_flags": (),
        "accepted_for_second_scale": True,
    }
    payload.update(updates)
    return QualityAssessment.model_validate(payload)


def segment(**updates: object) -> SensorSegment:
    payload: dict[str, object] = {
        "segment_id": "segment-fixture-001",
        "storage_layer": StorageLayer.RAW_IMMUTABLE,
        "participant_id": "participant-fixture-001",
        "site_id": "site-fixture-001",
        "device_id": "device-fixture-001",
        "session_id": "session-fixture-001",
        "profile": profile(),
        "started_at": datetime(2026, 8, 31, 8, 0, tzinfo=UTC),
        "source_relative_path": "fixtures/raw/segment-001.json",
        "source_sha256": SHA256,
        "parent_segment_id": None,
        "raw_immutable": True,
        "withdrawal_locator": "withdrawal-fixture-001",
        "quality": quality(),
        "samples": (
            SensorSample(
                sequence=0,
                utc_timestamp_ns=1_000_000_000,
                monotonic_timestamp_ns=10_000_000,
                values=(0.0, 0.1, 9.8, 0.0, 0.0, 0.0),
            ),
            SensorSample(
                sequence=1,
                utc_timestamp_ns=1_020_000_000,
                monotonic_timestamp_ns=30_000_000,
                values=(0.1, 0.1, 9.7, 0.01, 0.0, 0.0),
            ),
        ),
    }
    payload.update(updates)
    return SensorSegment.model_validate(payload)


def annotation(**updates: object) -> EventAnnotation:
    payload: dict[str, object] = {
        "event_id": "event-fixture-001",
        "participant_id": "participant-fixture-001",
        "site_id": "site-fixture-001",
        "device_id": "device-fixture-001",
        "session_id": "session-fixture-001",
        "event_type": EventType.ACCIDENTAL_FALL,
        "t_instability_ns": 2_000_000_000,
        "t_impact_ns": 2_200_000_000,
        "t_recovery_or_assist_ns": 4_000_000_000,
        "label_source": LabelSourceKind.ENGINEERING_FIXTURE,
        "adjudicator_ids": ("reviewer-fixture-001", "reviewer-fixture-002"),
        "confidence": LabelConfidence.HIGH,
        "synchronization_error_ms": 50,
        "notes": "只用于确定性工程合同验证。",
    }
    payload.update(updates)
    return EventAnnotation.model_validate(payload)


def test_valid_bundle_preserves_single_identity_and_quality_gate() -> None:
    bundle = ResearchRecordBundle(
        bundle_id="bundle-fixture-001",
        segments=(segment(),),
        annotations=(annotation(),),
    )

    assert bundle.segments[0].quality.accepted_for_second_scale is True


def test_wrong_units_and_missing_channels_are_rejected() -> None:
    with pytest.raises(ValidationError, match=r"必须使用 m/s\^2"):
        ChannelSpec(name="ax", quantity="acceleration", unit="rad/s")

    invalid_profile = profile().model_dump(mode="json")
    invalid_profile["channels"] = invalid_profile["channels"][:-1]
    with pytest.raises(ValidationError, match="通道顺序"):
        SensorProfile.model_validate(invalid_profile)


def test_out_of_order_or_duplicate_timestamps_are_rejected() -> None:
    invalid = segment().model_dump(mode="json")
    invalid["samples"][1]["utc_timestamp_ns"] = invalid["samples"][0][
        "utc_timestamp_ns"
    ]
    with pytest.raises(ValidationError, match="严格递增"):
        SensorSegment.model_validate(invalid)


def test_bad_clock_quality_cannot_enter_second_scale_bundle() -> None:
    low_quality_segment = segment(
        quality=quality(
            synchronization_error_ms=150,
            accepted_for_second_scale=False,
        )
    )
    with pytest.raises(ValidationError, match="不能进入数秒级研究包"):
        ResearchRecordBundle(
            bundle_id="bundle-fixture-001",
            segments=(low_quality_segment,),
            annotations=(),
        )


def test_cross_participant_or_device_bundle_is_rejected() -> None:
    with pytest.raises(ValidationError, match="不能混入不同参与者"):
        ResearchRecordBundle(
            bundle_id="bundle-fixture-001",
            segments=(segment(), segment(participant_id="participant-fixture-002")),
            annotations=(),
        )


def test_near_fall_cannot_have_impact_and_sync_error_must_pass_gate() -> None:
    with pytest.raises(ValidationError, match="不允许伪造撞击锚点"):
        annotation(event_type=EventType.NEAR_FALL)
    with pytest.raises(ValidationError, match="同步误差超过 100 ms"):
        annotation(synchronization_error_ms=101)
    with pytest.raises(ValidationError, match="必须记录 t_impact"):
        annotation(t_impact_ns=None)


def test_withdrawal_mapping_is_restricted_and_path_safe() -> None:
    entry = WithdrawalIndexEntry(
        withdrawal_locator="withdrawal-fixture-001",
        participant_id="participant-fixture-001",
        segment_ids=("segment-fixture-001",),
        event_ids=("event-fixture-001",),
        restricted_mapping_reference="controlled/withdrawal/map-001.ref",
    )
    assert entry.access_scope == "DATA_CONTROLLER_ONLY"

    with pytest.raises(ValidationError, match="安全相对引用"):
        WithdrawalIndexEntry(
            withdrawal_locator="withdrawal-fixture-001",
            participant_id="participant-fixture-001",
            segment_ids=(),
            event_ids=(),
            restricted_mapping_reference="../outside.json",
        )
