from __future__ import annotations

import argparse
import gc
import json
import subprocess
from pathlib import Path

from backend.app.training.activity import LABELS, load_participant_windows
from backend.scripts.train_activity_model import PROJECT_ROOT, _write_json, validate_recovery_catalog


DEFAULT_OUTPUT = Path("data/catalog/capture24_activity_availability_v1.json")


def select_disjoint_groups(
    scan_results: list[dict[str, object]],
    *,
    per_class_limit: int,
    train_count: int,
    evaluation_count: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    eligible = [
        str(item["participant_id"])
        for item in scan_results
        if all(
            int(dict(item["label_counts"]).get(label, 0)) >= per_class_limit
            for label in LABELS
        )
    ]
    required = train_count + evaluation_count
    if len(eligible) < required:
        raise ValueError(
            f"四类均达到固定上限的参与者不足：需要 {required}，实际 {len(eligible)}。"
        )
    return (
        tuple(eligible[:train_count]),
        tuple(eligible[train_count:required]),
    )


def scan(
    *,
    source_zip: Path,
    recovery_catalog_path: Path,
    source_commit: str,
    output_path: Path,
    per_class_limit: int,
    train_count: int,
    evaluation_count: int,
) -> dict[str, object]:
    subprocess.run(
        ["git", "cat-file", "-e", f"{source_commit}^{{commit}}"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
    )
    recovery = validate_recovery_catalog(
        source_zip=source_zip,
        recovery_catalog_path=recovery_catalog_path,
        participant_ids=(),
    )
    participants = tuple(str(item) for item in recovery["available_participants"])
    results: list[dict[str, object]] = []
    required = train_count + evaluation_count
    for index, participant_id in enumerate(participants, start=1):
        participant = load_participant_windows(
            source_zip,
            participant_id,
            per_class_limit=per_class_limit,
        )
        row = {
            "participant_id": participant_id,
            "label_counts": participant.label_counts,
            "window_count": len(participant.windows),
            "source_rows_scanned": participant.source_rows_scanned,
            "stopped_after_selection_complete": (
                participant.scan_stopped_after_selection_complete
            ),
            "eligible": all(
                participant.label_counts.get(label, 0) >= per_class_limit
                for label in LABELS
            ),
        }
        results.append(row)
        eligible_count = sum(bool(item["eligible"]) for item in results)
        print(
            f"participant={participant_id} index={index}/{len(participants)} "
            f"eligible={row['eligible']} eligible_count={eligible_count}/{required} "
            f"counts={participant.label_counts} rows={participant.source_rows_scanned}",
            flush=True,
        )
        del participant
        gc.collect()
        if eligible_count >= required:
            break

    training, evaluation = select_disjoint_groups(
        results,
        per_class_limit=per_class_limit,
        train_count=train_count,
        evaluation_count=evaluation_count,
    )
    scanned = {str(item["participant_id"]) for item in results}
    try:
        output_relative = output_path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError as error:
        raise ValueError("扫描报告必须写入项目目录内。") from error
    execution_command = (
        "python -m backend.scripts.scan_capture24_activity "
        f"--source-zip {recovery['source_zip_relative_path']} "
        f"--source-recovery-catalog {recovery['path']} "
        f"--source-commit {source_commit} --output {output_relative} "
        f"--per-class-limit {per_class_limit} --train-count {train_count} "
        f"--evaluation-count {evaluation_count}"
    )
    payload: dict[str, object] = {
        "format_version": "1.0.0",
        "dataset": "CAPTURE-24",
        "source_archive_scope": "recovered_official_prefix_subset",
        "source_recovery_catalog": recovery,
        "source_commit": source_commit,
        "execution_command": execution_command,
        "selection_policy": (
            "按恢复目录原始顺序扫描；只依据四个映射类别是否各取得固定数量的最先完整窗口。"
            "前 train_count 名合格参与者进入训练，随后 evaluation_count 名进入评估；"
            "不读取或比较任何模型预测与指标。"
        ),
        "per_class_limit": per_class_limit,
        "scan_results": results,
        "scanned_participant_count": len(results),
        "unscanned_participants": [
            item for item in participants if item not in scanned
        ],
        "training_participants": list(training),
        "evaluation_participants": list(evaluation),
        "participant_overlap": [],
        "limitations": [
            "来源只是 48 名完整成员的恢复前缀子集，不是完整 151 人数据包。",
            "扫描在取得所需合格人数后停止，未扫描者不代表缺少目标标签。",
            "标签可用性筛选不是模型性能筛选，且 CAPTURE-24 以年轻参与者为主。",
        ],
        "raw_or_window_data_committed": False,
    }
    _write_json(output_path.resolve(), payload)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="按固定标签可用性规则扫描 CAPTURE-24 恢复子集参与者。"
    )
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--source-recovery-catalog", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / DEFAULT_OUTPUT)
    parser.add_argument("--per-class-limit", type=int, default=20)
    parser.add_argument("--train-count", type=int, default=24)
    parser.add_argument("--evaluation-count", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.per_class_limit < 20:
        raise ValueError("标签可用性扫描的每类窗口上限不能低于 20。")
    if args.train_count < 1 or args.evaluation_count < 1:
        raise ValueError("训练和评估参与者数量必须为正整数。")
    result = scan(
        source_zip=args.source_zip,
        recovery_catalog_path=args.source_recovery_catalog,
        source_commit=args.source_commit,
        output_path=args.output,
        per_class_limit=args.per_class_limit,
        train_count=args.train_count,
        evaluation_count=args.evaluation_count,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
