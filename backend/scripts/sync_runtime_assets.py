from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from backend.app.contracts import (
    AgeGroup,
    CaseContract,
    CaseSourceFile,
    GroundTruthEvent,
    GroundTruthEventType,
    ImportRunContract,
    ModelKind,
    ModelManifest,
    RoutineEventContract,
    RoutineProfileContract,
    SelectionPolicy,
    SelectionRule,
    SensorKind,
    SensorStreamContract,
    SourceLicenseStatus,
    SourceFileRole,
    SourceReference,
    StorageFormat,
    TruthCategory,
)
from backend.app.database import Database, ImportCaseBundle


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUTINE_EVENTS_PATH = Path("data/cases/synthetic_routine_100_v1.json")
ROUTINE_MANIFEST_PATH = Path("models/routine_anomaly/statistical_v1/manifest.json")
FALL_MANIFEST_PATH = Path("models/fall_detector/tcn_final_candidate/manifest.json")
ACTIVITY_CATALOG_PATH = Path("data/catalog/capture24_activity_training_v1.json")
ACTIVITY_MANIFEST_PATH = Path(
    "models/activity_recognition/capture24_linear_v1/manifest.json"
)
CORE_PRODUCT_MANIFEST_PATHS = (
    FALL_MANIFEST_PATH,
    ROUTINE_MANIFEST_PATH,
    ACTIVITY_MANIFEST_PATH,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest(path: Path) -> ModelManifest:
    return ModelManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _sync_activity_demo_cases(database: Database) -> int:
    catalog_path = PROJECT_ROOT / ACTIVITY_CATALOG_PATH
    manifest_path = PROJECT_ROOT / ACTIVITY_MANIFEST_PATH
    if not catalog_path.is_file() or not manifest_path.is_file():
        return 0
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    records = catalog.get("demo_cases", [])
    if len(records) != 4:
        raise ValueError("CAPTURE-24 活动演示案例必须恰好覆盖四个映射类别。")
    manifest = _load_manifest(manifest_path)
    source_hash = catalog["source_zip_sha256"]
    recovery = catalog.get("source_recovery_catalog")
    if (
        catalog.get("source_archive_scope") != "recovered_official_prefix_subset"
        or not isinstance(recovery, dict)
        or recovery.get("source_zip_sha256") != source_hash
    ):
        raise ValueError("活动目录必须明确指向已核验的 CAPTURE-24 恢复前缀子集。")
    source = SourceReference(
        source_id=f"capture24-recovered-prefix-{source_hash[:12]}",
        dataset_name="CAPTURE-24",
        source_url="https://doi.org/10.5287/bodleian:NGx0JOMP5",
        fixed_version=f"sha256:{source_hash}",
        license_status=SourceLicenseStatus.VERIFIED_OPEN,
        license_reference=(
            "Scientific Data 2024 数据论文和 Oxford Research Archive 均声明数据为 CC BY 4.0。"
        ),
        redistribution_allowed=True,
        verified_at=manifest.created_at,
        notes=(
            f"官方不完整下载前缀中逐成员校验恢复的 {recovery['participant_count']} 人子集，"
            "不是完整 151 人数据包；自由生活腕部加速度数据以年轻参与者为主，"
            "案例年龄保持 UNKNOWN，不得描述为老人活动数据。"
        ),
    )
    catalog_hash = _sha256(catalog_path)
    import_run = ImportRunContract(
        run_id=f"capture24-activity-demo-v1-{source_hash[:12]}",
        source_id=source.source_id,
        importer_version="1.0.0",
        source_commit=manifest.source_commit,
        processing_source_commit=manifest.source_commit,
        selection_policy=SelectionPolicy(
            policy_id="fixed-first-evaluation-window-per-mapped-class-v1",
            total_count=4,
            rules=(
                SelectionRule(
                    age_group=AgeGroup.UNKNOWN,
                    truth_category=TruthCategory.REAL_FREE_LIVING,
                    count=4,
                ),
            ),
            ordering=(
                "固定评估参与者顺序中每个映射类别的第一个完整 20 秒窗口；"
                "不按预测是否正确或概率大小选择。"
            ),
        ),
        catalog_relative_path=ACTIVITY_CATALOG_PATH.as_posix(),
        catalog_sha256=catalog_hash,
        created_at=manifest.created_at,
    )
    bundles = []
    label_titles = {
        "walking": "走路",
        "eating_candidate": "进食候选",
        "sleep_or_lying_candidate": "睡眠或躺卧候选",
        "other_unknown": "其他或未知活动",
    }
    for record in records:
        case_id = record["case_id"]
        label = record["mapped_activity_label"]
        stream_id = f"{case_id}-accel"
        source_path = (
            f"{record['source_member']}#rows-"
            f"{record['source_start_row']}-{record['source_end_row']}"
        )
        case = CaseContract(
            case_id=case_id,
            title=f"CAPTURE-24 自由生活活动：{label_titles[label]}",
            description=(
                "从已核验恢复前缀子集的固定评估参与者组，按预先声明顺序选出的"
                "真实自由生活腕部加速度窗口；标签是候选映射，不代表医学状态，"
                "不代表老人数据，也不代表完整 CAPTURE-24。"
            ),
            truth_category=TruthCategory.REAL_FREE_LIVING,
            source=source,
            source_record_path=source_path,
            source_sha256=source_hash,
            participant_id=record["participant_id"],
            age_group=AgeGroup.UNKNOWN,
            device_name="Axivity AX3",
            wear_position="wrist_unspecified_side",
            original_sample_rate_hz=100,
            activity_label=label,
            has_accelerometer=True,
            has_gyroscope=False,
            allowed_models=(ModelKind.ACTIVITY_RECOGNITION,),
            processing_command=catalog["execution_command"],
            created_at=manifest.created_at,
            updated_at=manifest.created_at,
        )
        stream = SensorStreamContract(
            stream_id=stream_id,
            case_id=case_id,
            sensor_kind=SensorKind.ACCELEROMETER,
            sample_rate_hz=20,
            channels=("ax", "ay", "az"),
            units=("m/s^2", "m/s^2", "m/s^2"),
            sample_count=400,
            duration_ms=20_000,
            storage_format=StorageFormat.NPY,
            relative_path=record["processed_relative_path"],
            content_sha256=record["processed_sha256"],
            created_at=manifest.created_at,
        )
        source_file = CaseSourceFile(
            file_id=f"{case_id}-source",
            case_id=case_id,
            role=SourceFileRole.ACCELEROMETER,
            source_relative_path=record["source_member"],
            source_sha256=source_hash,
        )
        event = GroundTruthEvent(
            event_id=f"{case_id}-activity",
            case_id=case_id,
            event_type=GroundTruthEventType.ACTIVITY_INTERVAL,
            label=label,
            start_offset_ms=0,
            end_offset_ms=20_000,
            truth_category=TruthCategory.REAL_FREE_LIVING,
            annotation_source_sha256=source_hash,
            notes=(
                "标签来自 CAPTURE-24 自由生活注释和本项目保存的保守关键词映射；"
                "进食、睡眠或躺卧均保留候选含义；来源是恢复前缀子集，不是完整数据包。"
            ),
        )
        bundles.append(
            ImportCaseBundle(
                case=case,
                stream=stream,
                quality=None,
                source_files=(source_file,),
                ground_truth_events=(event,),
            )
        )
    database.import_case_bundles(
        source=source,
        import_run=import_run,
        bundles=tuple(bundles),
    )
    return len(bundles)


def sync(database_path: Path) -> dict[str, object]:
    database = Database(database_path)
    database.initialize()
    # The core product registry owns exactly the three ModelManifest contracts.
    # Isolated research models may keep their own manifests under models/ without
    # being misparsed as one of the production-facing three model kinds.
    manifest_paths = tuple(PROJECT_ROOT / path for path in CORE_PRODUCT_MANIFEST_PATHS)
    manifests = tuple(_load_manifest(path) for path in manifest_paths)
    for manifest in manifests:
        database.register_model_manifest(manifest)

    events_path = PROJECT_ROOT / ROUTINE_EVENTS_PATH
    events_payload = json.loads(events_path.read_text(encoding="utf-8"))
    events = tuple(
        RoutineEventContract.model_validate(item) for item in events_payload["events"]
    )
    routine_manifest = _load_manifest(PROJECT_ROOT / ROUTINE_MANIFEST_PATH)
    source = SourceReference(
        source_id="synthetic-routine-generator-v1",
        dataset_name="100 天合成生活规律",
        source_url="local://generated/synthetic-routine-v1",
        fixed_version=routine_manifest.source_commit,
        license_status=SourceLicenseStatus.LOCAL_RESEARCH_ONLY,
        license_reference=(
            "本项目独立确定性生成；本机需求参考压缩包没有明确代码许可证，未复制其源码。"
        ),
        redistribution_allowed=True,
        verified_at=routine_manifest.created_at,
        notes="固定种子生成的合成事件，不是真实老人生活记录。",
    )
    events_hash = _sha256(events_path)
    case = CaseContract(
        case_id=events_payload["profile_id"],
        title="100 天合成用餐、午睡与散步规律",
        description=(
            "固定种子生成的合成生活事件，仅用于演示个人规律规则；"
            "不代表任何真实老人或医学状态。"
        ),
        truth_category=TruthCategory.SYNTHETIC_ROUTINE,
        source=source,
        source_record_path=ROUTINE_EVENTS_PATH.as_posix(),
        source_sha256=events_hash,
        participant_id=None,
        age_group=AgeGroup.NOT_APPLICABLE,
        device_name="deterministic_synthetic_generator",
        wear_position="not_applicable",
        original_sample_rate_hz=None,
        activity_label="meal_nap_walk_routine",
        has_accelerometer=False,
        has_gyroscope=False,
        allowed_models=(ModelKind.ROUTINE_ANOMALY,),
        processing_command=(
            "python -m backend.scripts.build_routine_model "
            "--source-archive <local anomaly archive> --source-commit "
            f"{routine_manifest.source_commit}"
        ),
        created_at=routine_manifest.created_at,
        updated_at=routine_manifest.created_at,
    )
    history_start = date.fromisoformat(events_payload["history_start"])
    profile = RoutineProfileContract(
        profile_id=events_payload["profile_id"],
        case=case,
        history_start=history_start,
        history_end=history_start + timedelta(days=99),
        seed=events_payload["seed"],
        event_count=events_payload["event_count"],
        events_relative_path=ROUTINE_EVENTS_PATH.as_posix(),
        events_sha256=events_hash,
        created_at=routine_manifest.created_at,
    )
    database.register_routine_profile(source=source, profile=profile, events=events)
    activity_demo_case_count = _sync_activity_demo_cases(database)
    snapshot = database.snapshot()
    return {
        "database": str(database.path),
        "schema_version": snapshot.schema_version,
        "case_count": snapshot.case_count,
        "registered_manifests": [manifest.manifest_id for manifest in manifests],
        "routine_profile": profile.profile_id,
        "routine_event_count": len(events),
        "activity_demo_case_count": activity_demo_case_count,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把已核验模型与合成规律同步到本地 SQLite。")
    parser.add_argument(
        "--database",
        type=Path,
        default=PROJECT_ROOT / "backend" / "runtime" / "smartwatch.sqlite3",
    )
    return parser.parse_args()


def main() -> None:
    result = sync(parse_args().database)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
