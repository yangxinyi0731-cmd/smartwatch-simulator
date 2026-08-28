from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from ..contracts import (
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
    SourceLicenseStatus,
    SourceReference,
    StorageFormat,
    TruthCategory,
)
from ..database import Database, ImportCaseBundle


SOURCE_COMMIT = "74e0b93cb061d4ecbca12628f2d47090e97fbeea"
PROCESSING_SOURCE_COMMIT = "6c8bd6058f19467221e292c77a8df00630b8bd0b"
SOURCE_URL = "https://github.com/joaojtmarques/WEDA-FALL"
IMPORTER_VERSION = "1.0.0"
RUN_ID = "weda-fall-100-v1-74e0b93c"
TARGET_RATE_HZ = 50
MINIMUM_SAMPLES = 200
CHANNELS = ("ax", "ay", "az", "gx", "gy", "gz")
UNITS = ("m/s^2", "m/s^2", "m/s^2", "rad/s", "rad/s", "rad/s")
FILENAME_RE = re.compile(r"^(U\d{2})_R(\d{2})_accel\.csv$")

ACTIVITIES = {
    "F01": "行走时滑倒并向前跌倒",
    "F02": "行走时滑倒并向侧方跌倒",
    "F03": "行走时滑倒并向后跌倒",
    "F04": "行走时绊倒并向前跌倒",
    "F05": "尝试坐下时向后跌倒",
    "F06": "坐姿中向前跌倒",
    "F07": "坐姿中向后跌倒",
    "F08": "坐姿中向侧方跌倒",
    "D01": "走路",
    "D02": "慢跑",
    "D03": "上下楼梯",
    "D04": "坐椅、等待并起身",
    "D05": "尝试起身后坐回椅子",
    "D06": "蹲下系鞋带后起身",
    "D07": "行走时踉跄但未跌倒",
    "D08": "轻跳但未跌倒",
    "D09": "用手敲桌面",
    "D10": "拍手",
    "D11": "开关门",
}


@dataclass(frozen=True, slots=True)
class RecordingSource:
    recording_id: str
    activity_id: str
    subject_id: str
    trial_id: str
    accel_path: Path
    gyro_path: Path
    fall_start_s: float | None
    fall_end_s: float | None


@dataclass(frozen=True, slots=True)
class SensorQuality:
    rows: int
    unique_timestamps: int
    effective_rate_hz: float
    median_dt_ms: float
    max_gap_ms: float
    duplicate_timestamps: int


@dataclass(frozen=True, slots=True)
class ProcessedRecording:
    source: RecordingSource
    grid_start_s: float
    grid_end_s: float
    data: np.ndarray
    accel_quality: SensorQuality
    gyro_quality: SensorQuality
    quality_flags: tuple[str, ...]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def verify_source_checkout(raw_root: Path) -> None:
    raw_root = raw_root.resolve()
    if not (raw_root / ".git").exists():
        raise ValueError("WEDA-FALL 原始目录必须是保留 Git 元数据的固定版本检出。")
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=raw_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.stdout.strip() != SOURCE_COMMIT:
        raise ValueError(
            f"WEDA-FALL 版本不匹配；要求 {SOURCE_COMMIT}，实际 {completed.stdout.strip()}。"
        )
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=raw_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    if status:
        raise ValueError("WEDA-FALL 原始目录存在已跟踪改动，已拒绝导入。")


def load_fall_timestamps(path: Path) -> dict[str, tuple[float, float]]:
    result: dict[str, tuple[float, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = row["filename"].replace("\\", "/")
            start_s = float(row["start_time"])
            end_s = float(row["end_time"])
            if not math.isfinite(start_s) or not math.isfinite(end_s) or end_s <= start_s:
                raise ValueError(f"无效的跌倒时间标注：{key}")
            result[key] = (start_s, end_s)
    return result


def discover_recordings(raw_root: Path) -> tuple[RecordingSource, ...]:
    dataset_root = raw_root / "dataset"
    fifty_hz = dataset_root / "50Hz"
    timestamps = load_fall_timestamps(dataset_root / "fall_timestamps.csv")
    recordings: list[RecordingSource] = []
    for accel_path in sorted(fifty_hz.glob("*/*_accel.csv")):
        if accel_path.name.endswith("_vertical_accel.csv"):
            continue
        match = FILENAME_RE.fullmatch(accel_path.name)
        if match is None:
            raise ValueError(f"无法识别 WEDA-FALL 文件名：{accel_path.name}")
        activity_id = accel_path.parent.name
        subject_id, trial_number = match.groups()
        trial_id = f"R{trial_number}"
        recording_id = f"{activity_id}/{subject_id}_{trial_id}"
        gyro_path = accel_path.with_name(accel_path.name.replace("_accel.csv", "_gyro.csv"))
        if not gyro_path.is_file():
            raise FileNotFoundError(f"缺少配对陀螺仪文件：{gyro_path}")
        fall_interval = timestamps.get(recording_id)
        if activity_id.startswith("F") and fall_interval is None:
            raise ValueError(f"模拟跌倒记录缺少时间标注：{recording_id}")
        recordings.append(
            RecordingSource(
                recording_id=recording_id,
                activity_id=activity_id,
                subject_id=subject_id,
                trial_id=trial_id,
                accel_path=accel_path,
                gyro_path=gyro_path,
                fall_start_s=fall_interval[0] if fall_interval else None,
                fall_end_s=fall_interval[1] if fall_interval else None,
            )
        )
    if not recordings:
        raise ValueError("WEDA-FALL 原始目录中没有发现可导入记录。")
    return tuple(recordings)


def _read_sensor_csv(path: Path) -> tuple[np.ndarray, np.ndarray, SensorQuality]:
    values = np.genfromtxt(path, delimiter=",", skip_header=1, dtype=np.float64)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    if values.ndim != 2 or values.shape[1] != 4:
        raise ValueError(f"传感器文件必须有四列：{path}")
    if not np.isfinite(values).all():
        raise ValueError(f"传感器文件包含非有限数值：{path}")

    original_rows = len(values)
    order = np.argsort(values[:, 0], kind="stable")
    time_s = values[order, 0]
    xyz = values[order, 1:]
    unique_time, first, counts = np.unique(
        time_s, return_index=True, return_counts=True
    )
    if np.any(counts > 1):
        xyz = np.add.reduceat(xyz, first, axis=0) / counts[:, None]
        time_s = unique_time
    if len(time_s) < 2 or time_s[-1] <= time_s[0]:
        raise ValueError(f"传感器时间轴不可用：{path}")
    delta = np.diff(time_s)
    quality = SensorQuality(
        rows=original_rows,
        unique_timestamps=len(time_s),
        effective_rate_hz=float((len(time_s) - 1) / (time_s[-1] - time_s[0])),
        median_dt_ms=float(np.median(delta) * 1000),
        max_gap_ms=float(np.max(delta) * 1000),
        duplicate_timestamps=original_rows - len(time_s),
    )
    return time_s, xyz, quality


def _quality_flags(accel: SensorQuality, gyro: SensorQuality) -> tuple[str, ...]:
    flags: list[str] = []
    if accel.max_gap_ms > 100:
        flags.append("accel_gap_gt_100ms")
    if gyro.max_gap_ms > 100:
        flags.append("gyro_gap_gt_100ms")
    if accel.duplicate_timestamps:
        flags.append("accel_duplicate_timestamps")
    if gyro.duplicate_timestamps:
        flags.append("gyro_duplicate_timestamps")
    if abs(accel.effective_rate_hz - TARGET_RATE_HZ) / TARGET_RATE_HZ > 0.1:
        flags.append("accel_effective_rate_diff_gt_10pct")
    if abs(gyro.effective_rate_hz - TARGET_RATE_HZ) / TARGET_RATE_HZ > 0.1:
        flags.append("gyro_effective_rate_diff_gt_10pct")
    return tuple(flags)


def process_recording(source: RecordingSource) -> ProcessedRecording:
    accel_t, accel_xyz, accel_quality = _read_sensor_csv(source.accel_path)
    gyro_t, gyro_xyz, gyro_quality = _read_sensor_csv(source.gyro_path)
    start_s = max(float(accel_t[0]), float(gyro_t[0]))
    end_s = min(float(accel_t[-1]), float(gyro_t[-1]))
    grid_start_s = math.ceil((start_s - 1e-12) * TARGET_RATE_HZ) / TARGET_RATE_HZ
    grid_end_s = math.floor((end_s + 1e-12) * TARGET_RATE_HZ) / TARGET_RATE_HZ
    if grid_end_s <= grid_start_s:
        raise ValueError(f"两个传感器没有公共时间段：{source.recording_id}")
    sample_count = int(round((grid_end_s - grid_start_s) * TARGET_RATE_HZ)) + 1
    time_s = grid_start_s + np.arange(sample_count, dtype=np.float64) / TARGET_RATE_HZ
    channels = [
        np.interp(time_s, accel_t, accel_xyz[:, axis]) for axis in range(3)
    ] + [np.interp(time_s, gyro_t, gyro_xyz[:, axis]) for axis in range(3)]
    data = np.stack(channels, axis=1).astype(np.float32)
    if len(data) < MINIMUM_SAMPLES:
        raise ValueError(f"公共时间段少于 4 秒：{source.recording_id}")
    if not np.isfinite(data).all():
        raise ValueError(f"对齐后数据包含非有限数值：{source.recording_id}")
    if source.fall_start_s is not None and (
        source.fall_start_s < grid_start_s or source.fall_end_s > grid_end_s
    ):
        raise ValueError(f"跌倒标注超出公共传感器区间：{source.recording_id}")
    return ProcessedRecording(
        source=source,
        grid_start_s=grid_start_s,
        grid_end_s=grid_end_s,
        data=data,
        accel_quality=accel_quality,
        gyro_quality=gyro_quality,
        quality_flags=_quality_flags(accel_quality, gyro_quality),
    )


def _stratum(source: RecordingSource) -> str:
    if source.activity_id.startswith("F"):
        return "young_simulated_fall"
    if source.subject_id.startswith(("U2", "U3")):
        return "older_adl"
    return "young_adl"


def select_balanced(
    candidates: Sequence[RecordingSource],
    count: int,
) -> tuple[RecordingSource, ...]:
    remaining = list(candidates)
    subject_counts: Counter[str] = Counter()
    activity_counts: Counter[str] = Counter()
    selected: list[RecordingSource] = []
    while remaining and len(selected) < count:
        chosen = min(
            remaining,
            key=lambda item: (
                subject_counts[item.subject_id],
                activity_counts[item.activity_id],
                int(item.trial_id[1:]),
                item.subject_id,
                item.activity_id,
                item.recording_id,
            ),
        )
        remaining.remove(chosen)
        selected.append(chosen)
        subject_counts[chosen.subject_id] += 1
        activity_counts[chosen.activity_id] += 1
    if len(selected) != count:
        raise ValueError(f"可用记录不足：要求 {count}，实际 {len(selected)}。")
    return tuple(selected)


def select_policy_recordings(
    recordings: Sequence[RecordingSource],
) -> tuple[RecordingSource, ...]:
    quotas = {
        "young_simulated_fall": 40,
        "older_adl": 30,
        "young_adl": 30,
    }
    selected: list[RecordingSource] = []
    for stratum, count in quotas.items():
        selected.extend(
            select_balanced(
                [item for item in recordings if _stratum(item) == stratum],
                count,
            )
        )
    return tuple(sorted(selected, key=lambda item: item.recording_id))


def _write_npy_immutable(path: Path, data: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.save(handle, data, allow_pickle=False)
    new_hash = sha256_file(temporary)
    if path.exists():
        if sha256_file(path) != new_hash:
            temporary.unlink()
            raise ValueError(f"已存在的处理文件内容冲突：{path}")
        temporary.unlink()
    else:
        os.replace(temporary, path)
    return new_hash


def selection_policy() -> SelectionPolicy:
    return SelectionPolicy(
        policy_id="weda-balanced-40-fall-30-older-adl-30-young-adl-v1",
        total_count=100,
        rules=(
            SelectionRule(
                age_group=AgeGroup.YOUNG_ADULT,
                truth_category=TruthCategory.SIMULATED_FALL,
                count=40,
            ),
            SelectionRule(
                age_group=AgeGroup.OLDER_ADULT,
                truth_category=TruthCategory.REAL_LAB_ACTIVITY,
                count=30,
            ),
            SelectionRule(
                age_group=AgeGroup.YOUNG_ADULT,
                truth_category=TruthCategory.REAL_LAB_ACTIVITY,
                count=30,
            ),
        ),
        ordering=(
            "每个分层内按参与者已选数量、活动已选数量、试次、参与者、活动和记录标识"
            "依次最小化；仅选择具有真实加速度与陀螺仪配对的独立来源记录。"
        ),
    )


def source_reference(verified_at: datetime) -> SourceReference:
    return SourceReference(
        source_id="weda-fall-74e0b93c",
        dataset_name="WEDA-FALL",
        source_url=SOURCE_URL,
        fixed_version=SOURCE_COMMIT,
        license_status=SourceLicenseStatus.UNVERIFIED,
        license_reference="固定版本仓库中未发现可确认的开源许可证文件。",
        redistribution_allowed=None,
        verified_at=verified_at,
        notes=(
            "仅限本机研究核验；不提交或重新分发原始与处理后传感器文件。"
            "年轻参与者在受控床垫条件下模拟跌倒；老年参与者只执行日常活动。"
        ),
    )


def _case_identity(source: RecordingSource) -> tuple[str, str]:
    normalized = source.recording_id.replace("/", "-").lower()
    case_id = f"weda-{normalized}"
    return case_id, f"{case_id}-imu"


def _catalog_case_and_bundle(
    *,
    project_root: Path,
    raw_root: Path,
    processed: ProcessedRecording,
    source: SourceReference,
    created_at: datetime,
    annotation_hash: str,
) -> tuple[dict[str, object], ImportCaseBundle]:
    recording = processed.source
    case_id, stream_id = _case_identity(recording)
    relative_output = Path("data/processed/weda_fall_100") / recording.activity_id / (
        f"{recording.subject_id}_{recording.trial_id}.npy"
    )
    output_hash = _write_npy_immutable(project_root / relative_output, processed.data)
    accel_relative = recording.accel_path.relative_to(raw_root).as_posix()
    gyro_relative = recording.gyro_path.relative_to(raw_root).as_posix()
    accel_hash = sha256_file(recording.accel_path)
    gyro_hash = sha256_file(recording.gyro_path)
    is_fall = recording.activity_id.startswith("F")
    truth = TruthCategory.SIMULATED_FALL if is_fall else TruthCategory.REAL_LAB_ACTIVITY
    age_group = (
        AgeGroup.OLDER_ADULT
        if recording.subject_id.startswith(("U2", "U3"))
        else AgeGroup.YOUNG_ADULT
    )
    source_bundle = {
        "source_commit": SOURCE_COMMIT,
        "recording_id": recording.recording_id,
        "accel": {"path": accel_relative, "sha256": accel_hash},
        "gyro": {"path": gyro_relative, "sha256": gyro_hash},
        "fall_annotation": (
            {
                "path": "dataset/fall_timestamps.csv",
                "sha256": annotation_hash,
                "start_s": recording.fall_start_s,
                "end_s": recording.fall_end_s,
            }
            if is_fall
            else None
        ),
    }
    source_bundle_hash = sha256_json(source_bundle)
    if is_fall:
        title = f"年轻参与者受控床垫模拟跌倒：{recording.recording_id}"
        description = (
            "年轻参与者在受控床垫条件下执行的模拟跌倒，仅用于研究演示；"
            "不是现实生活中的老人跌倒。"
        )
    else:
        cohort = "老年参与者" if age_group is AgeGroup.OLDER_ADULT else "年轻参与者"
        title = f"{cohort}受控日常活动：{recording.recording_id}"
        description = (
            f"{cohort}在受控环境中执行的日常活动，用于跌倒模型误报分析；"
            "不代表跌倒事件。"
        )
    processing_command = (
        "python -m backend.scripts.import_weda_cases --raw-root <fixed WEDA-FALL checkout> "
        "--database backend/runtime/smartwatch.sqlite3"
    )
    case = CaseContract(
        case_id=case_id,
        title=title,
        description=description,
        truth_category=truth,
        source=source,
        source_record_path=f"dataset/50Hz/{recording.recording_id}",
        source_sha256=source_bundle_hash,
        participant_id=recording.subject_id,
        age_group=age_group,
        device_name="Fitbit Sense",
        wear_position="wrist_unspecified_side",
        original_sample_rate_hz=50,
        activity_label=recording.activity_id,
        has_accelerometer=True,
        has_gyroscope=True,
        allowed_models=(ModelKind.FALL_DETECTION,),
        processing_command=processing_command,
        created_at=created_at,
        updated_at=created_at,
    )
    duration_ms = int(round((len(processed.data) - 1) * 1000 / TARGET_RATE_HZ))
    stream = SensorStreamContract(
        stream_id=stream_id,
        case_id=case_id,
        sensor_kind=SensorKind.IMU_6AXIS,
        sample_rate_hz=TARGET_RATE_HZ,
        channels=CHANNELS,
        units=UNITS,
        sample_count=len(processed.data),
        duration_ms=duration_ms,
        storage_format=StorageFormat.NPY,
        relative_path=relative_output.as_posix(),
        content_sha256=output_hash,
        created_at=created_at,
    )
    quality = SensorQualityContract(
        stream_id=stream_id,
        accel_rows=processed.accel_quality.rows,
        accel_unique_timestamps=processed.accel_quality.unique_timestamps,
        gyro_rows=processed.gyro_quality.rows,
        gyro_unique_timestamps=processed.gyro_quality.unique_timestamps,
        accel_effective_rate_hz=processed.accel_quality.effective_rate_hz,
        gyro_effective_rate_hz=processed.gyro_quality.effective_rate_hz,
        accel_median_dt_ms=processed.accel_quality.median_dt_ms,
        gyro_median_dt_ms=processed.gyro_quality.median_dt_ms,
        accel_max_gap_ms=processed.accel_quality.max_gap_ms,
        gyro_max_gap_ms=processed.gyro_quality.max_gap_ms,
        flags=processed.quality_flags,
    )
    source_files = [
        CaseSourceFile(
            file_id=f"{case_id}-accel",
            case_id=case_id,
            role=SourceFileRole.ACCELEROMETER,
            source_relative_path=accel_relative,
            source_sha256=accel_hash,
        ),
        CaseSourceFile(
            file_id=f"{case_id}-gyro",
            case_id=case_id,
            role=SourceFileRole.GYROSCOPE,
            source_relative_path=gyro_relative,
            source_sha256=gyro_hash,
        ),
    ]
    if is_fall:
        source_files.append(
            CaseSourceFile(
                file_id=f"{case_id}-annotation",
                case_id=case_id,
                role=SourceFileRole.ANNOTATION,
                source_relative_path="dataset/fall_timestamps.csv",
                source_sha256=annotation_hash,
            )
        )
    events: list[GroundTruthEvent] = []
    if is_fall:
        assert recording.fall_start_s is not None and recording.fall_end_s is not None
        events.append(
            GroundTruthEvent(
                event_id=f"{case_id}-fall",
                case_id=case_id,
                event_type=GroundTruthEventType.FALL_INTERVAL,
                label=recording.activity_id,
                start_offset_ms=int(round((recording.fall_start_s - processed.grid_start_s) * 1000)),
                end_offset_ms=int(round((recording.fall_end_s - processed.grid_start_s) * 1000)),
                truth_category=TruthCategory.SIMULATED_FALL,
                annotation_source_sha256=annotation_hash,
                notes="年轻参与者在受控床垫条件下模拟的跌倒区间。",
            )
        )
    else:
        events.append(
            GroundTruthEvent(
                event_id=f"{case_id}-activity",
                case_id=case_id,
                event_type=GroundTruthEventType.ACTIVITY_INTERVAL,
                label=recording.activity_id,
                start_offset_ms=0,
                end_offset_ms=duration_ms,
                truth_category=TruthCategory.REAL_LAB_ACTIVITY,
                annotation_source_sha256=source_bundle_hash,
                notes="活动标签来自固定版本数据集的目录和记录命名。",
            )
        )
    bundle = ImportCaseBundle(
        case=case,
        stream=stream,
        quality=quality,
        source_files=tuple(source_files),
        ground_truth_events=tuple(events),
    )
    catalog_case = {
        "case": case.model_dump(mode="json"),
        "stream": stream.model_dump(mode="json"),
        "quality": quality.model_dump(mode="json"),
        "source_files": [item.model_dump(mode="json") for item in source_files],
        "ground_truth_events": [item.model_dump(mode="json") for item in events],
        "source_bundle": source_bundle,
        "grid_start_s": processed.grid_start_s,
        "grid_end_s": processed.grid_end_s,
    }
    return catalog_case, bundle


def _existing_created_at(catalog_path: Path) -> datetime | None:
    if not catalog_path.exists():
        return None
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    value = payload.get("created_at")
    if not isinstance(value, str):
        raise ValueError("现有目录文件缺少 created_at，已拒绝覆盖。")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _write_catalog_immutable(path: Path, payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError("现有案例目录与本次确定性导入结果不一致，已拒绝覆盖。")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
    return sha256_file(path)


def import_weda_cases(
    *,
    project_root: Path,
    raw_root: Path,
    database_path: Path,
    catalog_relative_path: Path = Path("data/catalog/weda_fall_100_v1.json"),
    created_at: datetime | None = None,
) -> dict[str, object]:
    project_root = project_root.resolve()
    raw_root = raw_root.resolve()
    database_path = database_path.resolve()
    catalog_path = project_root / catalog_relative_path
    verify_source_checkout(raw_root)
    existing_created_at = _existing_created_at(catalog_path)
    resolved_created_at = existing_created_at or created_at or datetime.now(UTC)
    if resolved_created_at.tzinfo is None:
        raise ValueError("created_at 必须包含时区。")
    source = source_reference(resolved_created_at)
    all_recordings = discover_recordings(raw_root)
    selected = select_policy_recordings(all_recordings)
    annotation_hash = sha256_file(raw_root / "dataset" / "fall_timestamps.csv")
    catalog_cases: list[dict[str, object]] = []
    bundles: list[ImportCaseBundle] = []
    for recording in selected:
        processed = process_recording(recording)
        catalog_case, bundle = _catalog_case_and_bundle(
            project_root=project_root,
            raw_root=raw_root,
            processed=processed,
            source=source,
            created_at=resolved_created_at,
            annotation_hash=annotation_hash,
        )
        catalog_cases.append(catalog_case)
        bundles.append(bundle)

    counts = Counter(
        (
            bundle.case.age_group.value,
            bundle.case.truth_category.value,
        )
        for bundle in bundles
    )
    catalog_payload: dict[str, object] = {
        "format_version": "1.0.0",
        "run_id": RUN_ID,
        "created_at": resolved_created_at.isoformat().replace("+00:00", "Z"),
        "source": source.model_dump(mode="json"),
        "importer_version": IMPORTER_VERSION,
        "processing_source_commit": PROCESSING_SOURCE_COMMIT,
        "selection_policy": selection_policy().model_dump(mode="json"),
        "counts": {
            f"{age_group}__{truth}": count
            for (age_group, truth), count in sorted(counts.items())
        },
        "case_count": len(bundles),
        "cases": catalog_cases,
        "data_handling": {
            "raw_and_processed_files_committed": False,
            "redistribution_allowed": None,
            "reason": "来源许可证未核验；传感器文件只保留在本机 Git 忽略目录。",
        },
    }
    catalog_hash = _write_catalog_immutable(catalog_path, catalog_payload)
    import_run = ImportRunContract(
        run_id=RUN_ID,
        source_id=source.source_id,
        importer_version=IMPORTER_VERSION,
        source_commit=SOURCE_COMMIT,
        processing_source_commit=PROCESSING_SOURCE_COMMIT,
        selection_policy=selection_policy(),
        catalog_relative_path=catalog_relative_path.as_posix(),
        catalog_sha256=catalog_hash,
        created_at=resolved_created_at,
    )
    database = Database(database_path)
    database.initialize()
    database.import_case_bundles(source=source, import_run=import_run, bundles=bundles)
    return {
        "run_id": RUN_ID,
        "catalog": catalog_relative_path.as_posix(),
        "catalog_sha256": catalog_hash,
        "database": str(database_path),
        "case_count": len(bundles),
        "counts": catalog_payload["counts"],
        "quality_flagged_case_count": sum(bool(item.quality.flags) for item in bundles),
    }


def summarize_subjects(recordings: Iterable[RecordingSource]) -> dict[str, int]:
    return dict(sorted(Counter(item.subject_id for item in recordings).items()))

