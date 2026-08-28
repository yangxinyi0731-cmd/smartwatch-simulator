from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from backend.app.contracts import (
    AgeGroup,
    CaseContract,
    CaseSourceFile,
    GroundTruthEvent,
    GroundTruthEventType,
    ImportRunContract,
    ModelKind,
    SelectionPolicy,
    SelectionRule,
    SensorKind,
    SensorQualityContract,
    SensorStreamContract,
    SourceFileRole,
    StorageFormat,
    TruthCategory,
)
from backend.app.database import Database, ImportCaseBundle
from backend.app.importers.weda import (
    RecordingSource,
    _read_sensor_csv,
    process_recording,
    select_balanced,
    source_reference,
)


NOW = datetime(2026, 8, 28, 9, 0, tzinfo=UTC)
SHA_A = "a" * 64
SHA_B = "b" * 64


def _write_sensor_fixture(path: Path, rows: list[tuple[float, float, float, float]]) -> None:
    path.write_text(
        "time,x,y,z\n"
        + "".join(
            f"{time_s},{x},{y},{z}\n" for time_s, x, y, z in rows
        ),
        encoding="utf-8",
    )


def test_sensor_reader_averages_duplicates_and_aligns_real_six_axis(
    tmp_path: Path,
) -> None:
    times = [index / 50 for index in range(251)]
    accel_rows = [(time_s, time_s, 1.0, 9.8) for time_s in times]
    accel_rows.insert(2, (times[1], 2.0, 3.0, 4.0))
    gyro_rows = [(time_s + 0.001, 0.1, 0.2, 0.3) for time_s in times]
    accel_path = tmp_path / "U01_R01_accel.csv"
    gyro_path = tmp_path / "U01_R01_gyro.csv"
    _write_sensor_fixture(accel_path, accel_rows)
    _write_sensor_fixture(gyro_path, gyro_rows)

    _, _, quality = _read_sensor_csv(accel_path)
    assert quality.rows == 252
    assert quality.unique_timestamps == 251
    assert quality.duplicate_timestamps == 1

    processed = process_recording(
        RecordingSource(
            recording_id="D01/U01_R01",
            activity_id="D01",
            subject_id="U01",
            trial_id="R01",
            accel_path=accel_path,
            gyro_path=gyro_path,
            fall_start_s=None,
            fall_end_s=None,
        )
    )
    assert processed.data.dtype == np.float32
    assert processed.data.shape[1] == 6
    assert len(processed.data) >= 200
    assert "accel_duplicate_timestamps" in processed.quality_flags


def test_balanced_selection_uses_distinct_source_recordings() -> None:
    candidates = tuple(
        RecordingSource(
            recording_id=f"D{activity:02d}/U{subject:02d}_R{trial:02d}",
            activity_id=f"D{activity:02d}",
            subject_id=f"U{subject:02d}",
            trial_id=f"R{trial:02d}",
            accel_path=Path("fixture") / f"a-{activity}-{subject}-{trial}.csv",
            gyro_path=Path("fixture") / f"g-{activity}-{subject}-{trial}.csv",
            fall_start_s=None,
            fall_end_s=None,
        )
        for activity in range(1, 4)
        for subject in range(1, 5)
        for trial in range(1, 3)
    )
    selected = select_balanced(candidates, 12)
    assert len(selected) == 12
    assert len({item.recording_id for item in selected}) == 12
    assert len({item.subject_id for item in selected}) == 4
    assert len({item.activity_id for item in selected}) == 3


def _bundle(*, source_hash: str = SHA_A) -> tuple[object, ImportRunContract, ImportCaseBundle]:
    source = source_reference(NOW)
    case = CaseContract(
        case_id="weda-test-case",
        title="年轻参与者受控日常活动测试夹具",
        description="自动测试夹具，不代表真实参与者记录。",
        truth_category=TruthCategory.REAL_LAB_ACTIVITY,
        source=source,
        source_record_path="dataset/50Hz/D01/U01_R01",
        source_sha256=source_hash,
        participant_id="U01",
        age_group=AgeGroup.YOUNG_ADULT,
        device_name="测试设备",
        wear_position="wrist_unspecified_side",
        original_sample_rate_hz=50,
        activity_label="D01",
        has_accelerometer=True,
        has_gyroscope=True,
        allowed_models=(ModelKind.FALL_DETECTION,),
        processing_command="pytest fixture",
        created_at=NOW,
        updated_at=NOW,
    )
    stream = SensorStreamContract(
        stream_id="weda-test-case-imu",
        case_id=case.case_id,
        sensor_kind=SensorKind.IMU_6AXIS,
        sample_rate_hz=50,
        channels=("ax", "ay", "az", "gx", "gy", "gz"),
        units=("m/s^2", "m/s^2", "m/s^2", "rad/s", "rad/s", "rad/s"),
        sample_count=200,
        duration_ms=3980,
        storage_format=StorageFormat.NPY,
        relative_path="data/processed/test.npy",
        content_sha256=SHA_A,
        created_at=NOW,
    )
    quality = SensorQualityContract(
        stream_id=stream.stream_id,
        accel_rows=201,
        accel_unique_timestamps=200,
        gyro_rows=200,
        gyro_unique_timestamps=200,
        accel_effective_rate_hz=50,
        gyro_effective_rate_hz=50,
        accel_median_dt_ms=20,
        gyro_median_dt_ms=20,
        accel_max_gap_ms=20,
        gyro_max_gap_ms=20,
        flags=("accel_duplicate_timestamps",),
    )
    bundle = ImportCaseBundle(
        case=case,
        stream=stream,
        quality=quality,
        source_files=(
            CaseSourceFile(
                file_id="weda-test-case-accel",
                case_id=case.case_id,
                role=SourceFileRole.ACCELEROMETER,
                source_relative_path="dataset/50Hz/D01/U01_R01_accel.csv",
                source_sha256=SHA_A,
            ),
            CaseSourceFile(
                file_id="weda-test-case-gyro",
                case_id=case.case_id,
                role=SourceFileRole.GYROSCOPE,
                source_relative_path="dataset/50Hz/D01/U01_R01_gyro.csv",
                source_sha256=SHA_B,
            ),
        ),
        ground_truth_events=(
            GroundTruthEvent(
                event_id="weda-test-case-activity",
                case_id=case.case_id,
                event_type=GroundTruthEventType.ACTIVITY_INTERVAL,
                label="D01",
                start_offset_ms=0,
                end_offset_ms=3980,
                truth_category=TruthCategory.REAL_LAB_ACTIVITY,
                annotation_source_sha256=SHA_A,
                notes="自动测试夹具标签。",
            ),
        ),
    )
    run = ImportRunContract(
        run_id="weda-test-run",
        source_id=source.source_id,
        importer_version="test",
        source_commit="c" * 40,
        processing_source_commit="d" * 40,
        selection_policy=SelectionPolicy(
            policy_id="test-one",
            total_count=1,
            rules=(
                SelectionRule(
                    age_group=AgeGroup.YOUNG_ADULT,
                    truth_category=TruthCategory.REAL_LAB_ACTIVITY,
                    count=1,
                ),
            ),
            ordering="固定单条测试夹具。",
        ),
        catalog_relative_path="data/catalog/test.json",
        catalog_sha256=SHA_A,
        created_at=NOW,
    )
    return source, run, bundle


def test_database_import_is_idempotent_and_conflicts_are_atomic(tmp_path: Path) -> None:
    database = Database(tmp_path / "import.sqlite3")
    database.initialize()
    source, run, bundle = _bundle()
    database.import_case_bundles(source=source, import_run=run, bundles=(bundle,))
    database.import_case_bundles(source=source, import_run=run, bundles=(bundle,))

    with sqlite3.connect(database.path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM import_runs").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM case_source_files").fetchone()[0] == 2

    conflicting_source, conflicting_run, conflicting_bundle = _bundle(source_hash=SHA_B)
    with pytest.raises(ValueError, match="内容冲突"):
        database.import_case_bundles(
            source=conflicting_source,
            import_run=conflicting_run,
            bundles=(conflicting_bundle,),
        )
    with sqlite3.connect(database.path) as connection:
        stored_hash = connection.execute(
            "SELECT source_sha256 FROM cases WHERE case_id = 'weda-test-case'"
        ).fetchone()[0]
    assert stored_hash == SHA_A
