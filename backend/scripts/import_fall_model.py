from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from backend.app.contracts import (
    ApprovalStatus,
    ManifestFormat,
    ModelKind,
    ModelManifest,
    TruthCategory,
    model_contracts,
)
from backend.app.database import Database


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_SOURCE_COMMIT = "6c8bd6058f19467221e292c77a8df00630b8bd0b"
EXPECTED_ARTIFACT_SHA256 = "1e214ebd89fce6620cf09a7a071aa904cd5ca0932e960181ce43c3695e212a3f"
DESTINATION = Path("models/fall_detector/tcn_final_candidate")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git(source_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=source_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _copy_immutable(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256_file(source) != sha256_file(destination):
            raise ValueError(f"目标模型文件已存在但哈希冲突：{destination}")
        return
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def import_model(source_root: Path) -> ModelManifest:
    source_root = source_root.resolve()
    if _git(source_root, "rev-parse", "HEAD") != EXPECTED_SOURCE_COMMIT:
        raise ValueError("跌倒模型来源仓库提交与固定版本不一致。")
    if _git(source_root, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("跌倒模型来源仓库存在已跟踪改动，已拒绝导入。")
    source_directory = source_root / "models" / "fall_detector" / "tcn_final_candidate"
    source_manifest_path = source_directory / "manifest.json"
    source_artifact_path = source_directory / "model.onnx"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    if source_manifest["artifact_sha256"] != EXPECTED_ARTIFACT_SHA256:
        raise ValueError("来源 manifest 中的跌倒模型哈希不符合固定记录。")
    if sha256_file(source_artifact_path) != EXPECTED_ARTIFACT_SHA256:
        raise ValueError("来源跌倒 ONNX 文件哈希不符合固定记录。")
    if source_manifest["deployment_approved"] is not False:
        raise ValueError("来源跌倒模型不得标记为已获部署批准。")
    if source_manifest["data_truth"] != {
        "falls": "young participants simulating falls on a mattress",
        "elder_participants": "ADL only; no fall trials",
    }:
        raise ValueError("来源跌倒模型的真实性声明发生变化，需人工复核。")

    destination = PROJECT_ROOT / DESTINATION
    _copy_immutable(source_artifact_path, destination / "model.onnx")
    _copy_immutable(source_manifest_path, destination / "source_manifest.json")
    committed_at = datetime.fromisoformat(
        _git(source_root, "show", "-s", "--format=%cI", EXPECTED_SOURCE_COMMIT)
    )
    contract = next(
        item
        for item in model_contracts()
        if item.model_kind is ModelKind.FALL_DETECTION
    )
    manifest = ModelManifest(
        manifest_id="fall-detector-tcn-0.2.0-dev",
        model_id="fall_detector_tcn_final_candidate",
        model_kind=ModelKind.FALL_DETECTION,
        version="0.2.0-dev",
        format=ManifestFormat.ONNX,
        source_commit=EXPECTED_SOURCE_COMMIT,
        artifact_relative_path=(DESTINATION / "model.onnx").as_posix(),
        artifact_sha256=EXPECTED_ARTIFACT_SHA256,
        contract=contract,
        training_truth_categories=(
            TruthCategory.REAL_LAB_ACTIVITY,
            TruthCategory.SIMULATED_FALL,
        ),
        training_data_references=(
            "WEDA-FALL fixed commit 74e0b93cb061d4ecbca12628f2d47090e97fbeea",
        ),
        evaluation_reference=(
            "来源仓库 reports/tcn_loso_metrics.json 与 reports/tcn_threshold_sweep.json；"
            "本平台另行保存 100 案例重放评估。"
        ),
        limitations=(
            "跌倒样本仅来自年轻参与者在床垫上的受控模拟。",
            "老年参与者只有日常活动，没有老人跌倒样本。",
            "尚无外部数据集、长期自由生活或真实设备验收。",
            "0.7 阈值是查看 WEDA-FALL 开发标签后的后验工作点，需要外部确认。",
        ),
        deployment_approved=False,
        approval_status=ApprovalStatus.EXTERNAL_VALIDATION_REQUIRED,
        external_validation_completed=False,
        created_at=committed_at,
    )
    manifest_path = destination / "manifest.json"
    serialized = manifest.model_dump_json(indent=2) + "\n"
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != serialized:
        raise ValueError("现有平台跌倒 manifest 与固定导入结果冲突。")
    manifest_path.write_text(serialized, encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="核验并导入固定版本跌倒 ONNX。")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--database",
        type=Path,
        default=PROJECT_ROOT / "backend" / "runtime" / "smartwatch.sqlite3",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = import_model(args.source_root)
    database = Database(args.database)
    database.initialize()
    database.register_model_manifest(manifest)
    print(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
