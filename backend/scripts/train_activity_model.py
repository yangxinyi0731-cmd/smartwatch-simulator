from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort

from backend.app.contracts import (
    ApprovalStatus,
    ManifestFormat,
    ModelKind,
    ModelManifest,
    TruthCategory,
    model_contracts,
)
from backend.app.training.activity import (
    LABELS,
    build_onnx,
    classification_metrics,
    combine_participants,
    load_participant_windows,
    predict_softmax,
    train_softmax,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_URL = "https://doi.org/10.5287/bodleian:NGx0JOMP5"
SOURCE_PAPER = "https://doi.org/10.1038/s41597-024-03960-3"
DATA_LICENSE = "CC BY 4.0"
MODEL_DIRECTORY = Path("models/activity_recognition/capture24_linear_v1")
CATALOG_PATH = Path("data/catalog/capture24_activity_training_v1.json")
REPORT_PATH = Path("reports/models/activity_capture24_group_holdout.json")
DEMO_DIRECTORY = Path("data/processed/capture24_activity_demo")
DEFAULT_TRAIN_PARTICIPANTS = tuple(f"P{index:03d}" for index in range(1, 25))
DEFAULT_EVALUATION_PARTICIPANTS = tuple(f"P{index:03d}" for index in range(102, 114))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return _sha256(path)


def _parse_participants(value: str) -> tuple[str, ...]:
    result = tuple(item.strip().upper() for item in value.split(",") if item.strip())
    if not result or any(len(item) != 4 or not item.startswith("P") or not item[1:].isdigit() for item in result):
        raise argparse.ArgumentTypeError("参与者必须使用逗号分隔的 P001 格式。")
    if len(set(result)) != len(result):
        raise argparse.ArgumentTypeError("参与者列表不能重复。")
    return result


def validate_recovery_catalog(
    *,
    source_zip: Path,
    recovery_catalog_path: Path,
    participant_ids: tuple[str, ...],
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    project_root = project_root.resolve()
    source_zip = source_zip.resolve()
    recovery_catalog_path = recovery_catalog_path.resolve()
    try:
        source_relative = source_zip.relative_to(project_root).as_posix()
        catalog_relative = recovery_catalog_path.relative_to(project_root).as_posix()
    except ValueError as error:
        raise ValueError("来源 ZIP 和恢复目录必须位于项目目录内。") from error
    payload = json.loads(recovery_catalog_path.read_text(encoding="utf-8"))
    if payload.get("dataset") != "CAPTURE-24":
        raise ValueError("恢复目录的数据集必须是 CAPTURE-24。")
    if payload.get("raw_or_recovered_data_committed") is not False:
        raise ValueError("恢复目录必须明确 raw_or_recovered_data_committed=false。")
    source_hash = _sha256(source_zip)
    if payload.get("recovered_zip_relative_path") != source_relative:
        raise ValueError("恢复目录中的 ZIP 相对路径与训练来源不一致。")
    if payload.get("recovered_zip_sha256") != source_hash:
        raise ValueError("恢复目录中的 ZIP SHA-256 与训练来源不一致。")
    if payload.get("recovered_zip_bytes") != source_zip.stat().st_size:
        raise ValueError("恢复目录中的 ZIP 字节数与训练来源不一致。")
    available = payload.get("participants")
    if (
        not isinstance(available, list)
        or len(available) != len(set(available))
        or payload.get("participant_count") != len(available)
    ):
        raise ValueError("恢复目录中的参与者列表或数量无效。")
    missing = sorted(set(participant_ids) - set(available))
    if missing:
        raise ValueError(f"训练或评估参与者不在已恢复完整成员中：{missing}")
    return {
        "scope": "recovered_official_prefix_subset",
        "path": catalog_relative,
        "sha256": _sha256(recovery_catalog_path),
        "participant_count": len(available),
        "available_participants": available,
        "source_zip_relative_path": source_relative,
        "source_zip_sha256": source_hash,
        "source_zip_bytes": source_zip.stat().st_size,
        "official_declared_bytes": payload.get("official_declared_bytes"),
        "truncated_member_excluded": payload.get("truncated_member_excluded"),
    }


def _load_group(
    source_zip: Path,
    participant_ids: tuple[str, ...],
    per_class_limit: int,
    group_name: str,
):
    participants = []
    for index, participant_id in enumerate(participant_ids, start=1):
        participant = load_participant_windows(
            source_zip,
            participant_id,
            per_class_limit=per_class_limit,
        )
        participants.append(participant)
        print(
            f"group={group_name} participant={participant_id} "
            f"index={index}/{len(participant_ids)} windows={len(participant.windows)} "
            f"counts={participant.label_counts}",
            flush=True,
        )
    return tuple(participants)


def _group_summary(participants) -> dict[str, object]:
    label_counts: Counter[str] = Counter()
    raw_counts: Counter[str] = Counter()
    per_participant = {}
    for participant in participants:
        label_counts.update(participant.label_counts)
        raw_counts.update(participant.raw_annotation_counts)
        per_participant[participant.participant_id] = participant.label_counts
    raw_mapping_summary: dict[str, list[dict[str, object]]] = {label: [] for label in LABELS}
    from backend.app.training.activity import map_annotation

    for annotation, row_count in raw_counts.most_common():
        target = map_annotation(annotation)
        if target is not None and len(raw_mapping_summary[target]) < 25:
            raw_mapping_summary[target].append(
                {"raw_annotation": annotation, "source_row_count": row_count}
            )
    return {
        "participants": [item.participant_id for item in participants],
        "window_counts": dict(sorted(label_counts.items())),
        "per_participant_window_counts": per_participant,
        "top_raw_annotations_by_target": raw_mapping_summary,
        "annotation_count_scope": (
            "rows scanned until every mapped class reached its fixed cap, or end of member"
        ),
        "scan": {
            item.participant_id: {
                "source_rows_scanned": item.source_rows_scanned,
                "stopped_after_selection_complete": (
                    item.scan_stopped_after_selection_complete
                ),
            }
            for item in participants
        },
    }


def _write_demo_cases(
    participants,
    session: ort.InferenceSession,
    *,
    source_zip_sha256: str,
) -> list[dict[str, object]]:
    selected: dict[str, tuple[object, int]] = {}
    for participant in participants:
        for index, label_index in enumerate(participant.labels):
            label = LABELS[int(label_index)]
            if label not in selected:
                selected[label] = (participant, index)
    missing = [label for label in LABELS if label not in selected]
    if missing:
        raise ValueError(f"评估参与者缺少活动演示窗口：{missing}")

    demo_directory = PROJECT_ROOT / DEMO_DIRECTORY
    demo_directory.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, object]] = []
    for label in LABELS:
        participant, index = selected[label]
        window = participant.windows[index].astype(np.float32)
        reference = participant.references[index]
        relative_path = DEMO_DIRECTORY / f"{label}-{participant.participant_id}.npy"
        output_path = PROJECT_ROOT / relative_path
        np.save(output_path, window, allow_pickle=False)
        probabilities = session.run(
            ["activity_probabilities"],
            {"acceleration_window": window[None, ...]},
        )[0][0]
        prediction_index = int(np.argmax(probabilities))
        records.append(
            {
                "case_id": f"capture24-{label.replace('_', '-')}-{participant.participant_id.lower()}",
                "participant_id": participant.participant_id,
                "truth_category": "REAL_FREE_LIVING",
                "mapped_activity_label": label,
                "selection_policy": (
                    "固定评估参与者顺序中该映射类别的第一个完整 20 秒窗口；"
                    "不按预测正确与否或置信度挑选。"
                ),
                "source_zip_sha256": source_zip_sha256,
                "source_member": reference.source_member,
                "source_start_row": reference.source_start_row,
                "source_end_row": reference.source_end_row,
                "processed_relative_path": relative_path.as_posix(),
                "processed_sha256": _sha256(output_path),
                "processed_shape": list(window.shape),
                "processed_rate_hz": 20,
                "processed_units": ["m/s^2", "m/s^2", "m/s^2"],
                "model_output": {
                    "predicted_label": LABELS[prediction_index],
                    "probabilities": {
                        name: float(probabilities[class_index])
                        for class_index, name in enumerate(LABELS)
                    },
                },
            }
        )
    return records


def train(
    *,
    source_zip: Path,
    source_recovery_catalog: Path,
    source_commit: str,
    train_participants: tuple[str, ...],
    evaluation_participants: tuple[str, ...],
    per_class_limit: int,
) -> dict[str, object]:
    source_zip = source_zip.resolve()
    if set(train_participants) & set(evaluation_participants):
        raise ValueError("训练和评估参与者不能重叠。")
    subprocess.run(
        ["git", "cat-file", "-e", f"{source_commit}^{{commit}}"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    committed_at = datetime.fromisoformat(
        subprocess.run(
            ["git", "show", "-s", "--format=%cI", source_commit],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        ).stdout.strip()
    )
    recovery_provenance = validate_recovery_catalog(
        source_zip=source_zip,
        recovery_catalog_path=source_recovery_catalog,
        participant_ids=train_participants + evaluation_participants,
    )
    source_hash = str(recovery_provenance["source_zip_sha256"])
    print(
        f"source_sha256={source_hash} bytes={source_zip.stat().st_size} "
        f"scope={recovery_provenance['scope']}",
        flush=True,
    )
    training = _load_group(
        source_zip, train_participants, per_class_limit, "training"
    )
    evaluation = _load_group(
        source_zip, evaluation_participants, per_class_limit, "evaluation"
    )
    train_x, train_y, train_groups = combine_participants(training)
    eval_x, eval_y, eval_groups = combine_participants(evaluation)
    if set(train_groups) & set(eval_groups):
        raise RuntimeError("参与者分组泄漏。")
    train_counts = np.bincount(train_y, minlength=len(LABELS))
    eval_counts = np.bincount(eval_y, minlength=len(LABELS))
    if np.any(train_counts < 20) or np.any(eval_counts < 20):
        raise ValueError(
            f"四类窗口不足；训练={train_counts.tolist()} 评估={eval_counts.tolist()}。"
        )

    model = train_softmax(train_x, train_y)
    model_directory = PROJECT_ROOT / MODEL_DIRECTORY
    artifact_path = model_directory / "model.onnx"
    build_onnx(model, artifact_path)
    onnx.checker.check_model(onnx.load(artifact_path))
    session = ort.InferenceSession(str(artifact_path), providers=["CPUExecutionProvider"])
    runtime_probabilities = session.run(
        ["activity_probabilities"],
        {"acceleration_window": eval_x.astype(np.float32)},
    )[0]
    numpy_probabilities = predict_softmax(model, eval_x)
    onnx_max_abs_error = float(
        np.max(np.abs(runtime_probabilities - numpy_probabilities))
    )
    if onnx_max_abs_error > 1e-5:
        raise RuntimeError(f"ONNX 与 NumPy 输出误差过大：{onnx_max_abs_error}")
    metrics = classification_metrics(eval_y, runtime_probabilities)
    training_metrics = classification_metrics(train_y, predict_softmax(model, train_x))
    artifact_hash = _sha256(artifact_path)
    demo_cases = _write_demo_cases(
        evaluation,
        session,
        source_zip_sha256=source_hash,
    )
    execution_command = (
        "python -m backend.scripts.train_activity_model "
        f"--source-zip {recovery_provenance['source_zip_relative_path']} "
        f"--source-recovery-catalog {recovery_provenance['path']} "
        f"--source-commit {source_commit} "
        f"--train-participants {','.join(train_participants)} "
        f"--evaluation-participants {','.join(evaluation_participants)} "
        f"--per-class-limit {per_class_limit}"
    )
    catalog = {
        "format_version": "1.0.0",
        "dataset": "CAPTURE-24",
        "source_url": SOURCE_URL,
        "paper": SOURCE_PAPER,
        "license": DATA_LICENSE,
        "attribution": (
            "Chan S, Hang Y, Tong C, et al. CAPTURE-24: A large dataset of "
            "wrist-worn activity tracker data collected in the wild for human "
            "activity recognition. Scientific Data 11, 1135 (2024)."
        ),
        "source_zip_sha256": source_hash,
        "source_zip_bytes": source_zip.stat().st_size,
        "source_archive_scope": recovery_provenance["scope"],
        "source_recovery_catalog": recovery_provenance,
        "source_device": "Axivity AX3 wrist-worn accelerometer",
        "source_rate_hz": 100,
        "source_units": "g",
        "processing": {
            "window_seconds": 20,
            "target_rate_hz": 20,
            "anti_alias": "non-overlapping five-sample boxcar mean before decimation",
            "target_units": "m/s^2",
            "per_participant_per_class_limit": per_class_limit,
            "annotation_mapping": (
                "case-insensitive conservative rules: sleep/asleep/lying/lie down/in bed; "
                "explicit semicolon eating/drinking category; walking category/description; "
                "all other annotated activities to other_unknown. Phrases such as with-or-without-"
                "eating are not treated as eating labels."
            ),
        },
        "training_group": _group_summary(training),
        "evaluation_group": _group_summary(evaluation),
        "demo_cases": demo_cases,
        "execution_command": execution_command,
        "raw_or_window_data_committed": False,
    }
    catalog_path = PROJECT_ROOT / CATALOG_PATH
    catalog_hash = _write_json(catalog_path, catalog)
    report = {
        "report_version": "1.0.0",
        "execution_command": execution_command,
        "source_catalog": {
            "path": CATALOG_PATH.as_posix(),
            "sha256": catalog_hash,
        },
        "source_recovery_catalog": recovery_provenance,
        "split": {
            "method": "fixed disjoint participant groups",
            "training_participants": list(train_participants),
            "evaluation_participants": list(evaluation_participants),
            "overlap": [],
        },
        "training": {
            "window_count": len(train_y),
            "class_counts": {
                label: int(train_counts[index]) for index, label in enumerate(LABELS)
            },
            "iterations": 1200,
            "learning_rate": 0.05,
            "l2": 0.001,
            "final_weighted_loss": model.final_loss,
            "resubstitution_metrics": training_metrics,
        },
        "evaluation": {
            "window_count": len(eval_y),
            "class_counts": {
                label: int(eval_counts[index]) for index, label in enumerate(LABELS)
            },
            "participant_group_holdout_metrics": metrics,
        },
        "onnx": {
            "artifact_sha256": artifact_hash,
            "onnx_version": onnx.__version__,
            "onnxruntime_version": ort.__version__,
            "providers": session.get_providers(),
            "max_abs_error_vs_numpy": onnx_max_abs_error,
        },
        "limitations": [
            "训练来源只是从官方不完整下载前缀恢复并逐成员校验的 48 人可用子集，不是完整 151 人数据包。",
            "CAPTURE-24 以年轻参与者为主，不能描述为老人活动数据。",
            "标签来自自由生活相机/睡眠日记注释和本项目显式关键词映射；进食与睡眠输出仍是候选。",
            "评估是同一数据集内未见参与者组，不是独立外部数据集验证。",
            "每名参与者每类窗口有固定上限，报告指标只适用于保存的选择与处理配置。",
            "模型未完成外部验证，deployment_approved=false。",
        ],
    }
    report_path = PROJECT_ROOT / REPORT_PATH
    _write_json(report_path, report)
    contract = next(
        item
        for item in model_contracts()
        if item.model_kind is ModelKind.ACTIVITY_RECOGNITION
    )
    manifest = ModelManifest(
        manifest_id="activity-capture24-linear-1.0.0",
        model_id="activity_capture24_linear_features",
        model_kind=ModelKind.ACTIVITY_RECOGNITION,
        version="1.0.0",
        format=ManifestFormat.ONNX,
        source_commit=source_commit,
        artifact_relative_path=(MODEL_DIRECTORY / "model.onnx").as_posix(),
        artifact_sha256=artifact_hash,
        contract=contract,
        training_truth_categories=(TruthCategory.REAL_FREE_LIVING,),
        training_data_references=(
            (
                "CAPTURE-24 recovered official prefix subset "
                f"sha256={source_hash}"
            ),
            (
                f"{recovery_provenance['path']} "
                f"sha256={recovery_provenance['sha256']}"
            ),
            f"{CATALOG_PATH.as_posix()} sha256={catalog_hash}",
        ),
        evaluation_reference=REPORT_PATH.as_posix(),
        limitations=tuple(report["limitations"]),
        deployment_approved=False,
        approval_status=ApprovalStatus.EXTERNAL_VALIDATION_REQUIRED,
        external_validation_completed=False,
        created_at=committed_at,
    )
    _write_json(model_directory / "manifest.json", manifest.model_dump(mode="json"))
    return {
        "manifest_id": manifest.manifest_id,
        "artifact_sha256": artifact_hash,
        "catalog_sha256": catalog_hash,
        "training_window_count": len(train_y),
        "evaluation_window_count": len(eval_y),
        "metrics": metrics,
        "onnx_max_abs_error": onnx_max_abs_error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练 CAPTURE-24 四类腕部活动候选模型。")
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--source-recovery-catalog", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument(
        "--train-participants",
        type=_parse_participants,
        default=DEFAULT_TRAIN_PARTICIPANTS,
    )
    parser.add_argument(
        "--evaluation-participants",
        type=_parse_participants,
        default=DEFAULT_EVALUATION_PARTICIPANTS,
    )
    parser.add_argument("--per-class-limit", type=int, default=80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.per_class_limit < 20:
        raise ValueError("每名参与者每类窗口上限不能低于 20。")
    result = train(
        source_zip=args.source_zip,
        source_recovery_catalog=args.source_recovery_catalog,
        source_commit=args.source_commit,
        train_participants=args.train_participants,
        evaluation_participants=args.evaluation_participants,
        per_class_limit=args.per_class_limit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
