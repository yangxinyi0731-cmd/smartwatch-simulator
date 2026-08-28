from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from backend.app.contracts import (
    AgeGroup,
    CaseContract,
    ModelKind,
    ModelManifest,
    RoutineEventContract,
    RoutineProfileContract,
    SourceLicenseStatus,
    SourceReference,
    TruthCategory,
)
from backend.app.database import Database


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUTINE_EVENTS_PATH = Path("data/cases/synthetic_routine_100_v1.json")
ROUTINE_MANIFEST_PATH = Path("models/routine_anomaly/statistical_v1/manifest.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_manifest(path: Path) -> ModelManifest:
    return ModelManifest.model_validate_json(path.read_text(encoding="utf-8"))


def sync(database_path: Path) -> dict[str, object]:
    database = Database(database_path)
    database.initialize()
    manifest_paths = tuple(sorted((PROJECT_ROOT / "models").glob("*/*/manifest.json")))
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
        history_end=history_start.fromordinal(history_start.toordinal() + 99),
        seed=events_payload["seed"],
        event_count=events_payload["event_count"],
        events_relative_path=ROUTINE_EVENTS_PATH.as_posix(),
        events_sha256=events_hash,
        created_at=routine_manifest.created_at,
    )
    database.register_routine_profile(source=source, profile=profile, events=events)
    snapshot = database.snapshot()
    return {
        "database": str(database.path),
        "schema_version": snapshot.schema_version,
        "case_count": snapshot.case_count,
        "registered_manifests": [manifest.manifest_id for manifest in manifests],
        "routine_profile": profile.profile_id,
        "routine_event_count": len(events),
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
