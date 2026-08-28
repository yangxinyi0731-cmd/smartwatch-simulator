from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import onnxruntime as ort

from backend.app.models.fall import FallModelAdapter
from backend.app.models.fall_evaluation import infer_case, overlaps


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = Path("data/catalog/weda_fall_100_v1.json")
DEFAULT_MANIFEST = Path("models/fall_detector/tcn_final_candidate/manifest.json")
DEFAULT_REPORT = Path("reports/models/fall_detector_tcn_100_cases.json")


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(
    *,
    catalog_path: Path,
    manifest_path: Path,
    evaluated_at: datetime | None = None,
) -> dict[str, object]:
    catalog_path = catalog_path.resolve()
    manifest_path = manifest_path.resolve()
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    adapter = FallModelAdapter(
        project_root=PROJECT_ROOT,
        manifest_path=manifest_path,
    )
    per_case: list[dict[str, object]] = []
    true_positive_fall_events = 0
    false_negative_fall_events = 0
    false_alarm_episodes = 0
    total_duration_s = 0.0
    elder_false_alarm_episodes = 0
    elder_duration_s = 0.0
    trial_matrix = [[0, 0], [0, 0]]
    distribution: Counter[str] = Counter()

    for item in catalog["cases"]:
        case = item["case"]
        stream = item["stream"]
        path = (PROJECT_ROOT / stream["relative_path"]).resolve()
        if _sha256(path) != stream["content_sha256"]:
            raise ValueError(f"案例处理文件哈希不一致：{case['case_id']}")
        data = np.load(path, allow_pickle=False)
        probabilities, episodes = infer_case(adapter, data)
        truth_fall = case["truth_category"] == "SIMULATED_FALL"
        fall_events = [
            event
            for event in item["ground_truth_events"]
            if event["event_type"] == "FALL_INTERVAL"
        ]
        if truth_fall and len(fall_events) != 1:
            raise ValueError(f"模拟跌倒案例必须恰有一个跌倒区间：{case['case_id']}")
        fall_event = fall_events[0] if fall_events else None
        overlapping = (
            [
                episode
                for episode in episodes
                if overlaps(
                    episode,
                    int(fall_event["start_offset_ms"]),
                    int(fall_event["end_offset_ms"]),
                )
            ]
            if fall_event
            else []
        )
        detected = bool(overlapping)
        if truth_fall:
            if detected:
                true_positive_fall_events += 1
            else:
                false_negative_fall_events += 1
        case_false_alarms = len(episodes) - len(overlapping)
        false_alarm_episodes += case_false_alarms
        predicted_fall_trial = bool(episodes)
        trial_matrix[int(truth_fall)][int(predicted_fall_trial)] += 1
        duration_s = float(stream["duration_ms"]) / 1000
        total_duration_s += duration_s
        if case["age_group"] == "OLDER_ADULT":
            elder_false_alarm_episodes += len(episodes)
            elder_duration_s += duration_s
        distribution[f"{case['age_group']}__{case['truth_category']}"] += 1
        per_case.append(
            {
                "case_id": case["case_id"],
                "age_group": case["age_group"],
                "truth_category": case["truth_category"],
                "activity_label": case["activity_label"],
                "window_count": len(probabilities),
                "max_fall_probability": (
                    float(np.max(probabilities)) if len(probabilities) else None
                ),
                "alarm_episode_count": len(episodes),
                "false_alarm_episode_count": case_false_alarms,
                "fall_event_detected": detected if truth_fall else None,
                "episodes": [
                    {
                        "start_offset_ms": episode.start_offset_ms,
                        "end_offset_ms": episode.end_offset_ms,
                        "peak_probability": episode.peak_probability,
                        "window_count": episode.window_count,
                    }
                    for episode in episodes
                ],
            }
        )

    event_precision = _ratio(
        true_positive_fall_events,
        true_positive_fall_events + false_alarm_episodes,
    )
    event_recall = _ratio(
        true_positive_fall_events,
        true_positive_fall_events + false_negative_fall_events,
    )
    event_f1 = (
        2 * event_precision * event_recall / (event_precision + event_recall)
        if event_precision is not None
        and event_recall is not None
        and event_precision + event_recall > 0
        else None
    )
    resolved_time = evaluated_at or datetime.now(UTC)
    return {
        "report_version": "1.0.0",
        "evaluated_at": resolved_time.isoformat().replace("+00:00", "Z"),
        "execution_command": (
            "python -m backend.scripts.evaluate_fall_model "
            "--catalog data/catalog/weda_fall_100_v1.json "
            "--manifest models/fall_detector/tcn_final_candidate/manifest.json "
            "--report reports/models/fall_detector_tcn_100_cases.json"
        ),
        "runtime": {
            "onnxruntime_version": ort.__version__,
            "providers": adapter.session.get_providers(),
        },
        "model": {
            "manifest_id": adapter.manifest.manifest_id,
            "artifact_sha256": adapter.manifest.artifact_sha256,
            "threshold": adapter.threshold,
            "deployment_approved": adapter.manifest.deployment_approved,
        },
        "dataset": {
            "catalog_relative_path": catalog_path.relative_to(PROJECT_ROOT).as_posix(),
            "catalog_sha256": _sha256(catalog_path),
            "case_count": len(per_case),
            "distribution": dict(sorted(distribution.items())),
            "relationship_to_training": (
                "同一 WEDA-FALL 来源；交付 ONNX 在全部 WEDA-FALL 参与者上重新拟合，"
                "因此本报告只是本机重放行为核验，不是独立泛化评估。"
            ),
        },
        "event_metrics": {
            "true_positive_simulated_fall_events": true_positive_fall_events,
            "false_negative_simulated_fall_events": false_negative_fall_events,
            "false_alarm_episodes": false_alarm_episodes,
            "event_precision": event_precision,
            "event_recall": event_recall,
            "event_f1": event_f1,
            "false_alarms_per_scripted_replay_hour": (
                false_alarm_episodes * 3600 / total_duration_s
            ),
            "evaluated_scripted_duration_s": total_duration_s,
            "trial_confusion_matrix": {
                "labels": ["adl_trial", "simulated_fall_trial"],
                "matrix": trial_matrix,
            },
        },
        "older_adl_false_alarm_analysis": {
            "case_count": sum(
                item["age_group"] == "OLDER_ADULT" for item in per_case
            ),
            "false_alarm_episodes": elder_false_alarm_episodes,
            "false_alarms_per_scripted_replay_hour": (
                elder_false_alarm_episodes * 3600 / elder_duration_s
            ),
            "evaluated_scripted_duration_s": elder_duration_s,
            "meaning": "仅分析老年参与者受控日常活动误报；没有老人跌倒样本。",
        },
        "limitations": [
            "40 个跌倒案例均为年轻参与者在受控床垫条件下模拟。",
            "30 个老人案例全部是受控日常活动，只能用于误报分析。",
            "模型已在同一数据集的全部参与者上重新拟合，本报告不能作为外部测试准确率。",
            "每小时误报分母是短时脚本回放时长，不能外推为自然生活每天误报数。",
            "模型未完成外部验证，deployment_approved=false。",
        ],
        "cases": per_case,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="重放 100 个案例并保存跌倒模型实测报告。")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = evaluate(
        catalog_path=PROJECT_ROOT / args.catalog,
        manifest_path=PROJECT_ROOT / args.manifest,
    )
    report_path = PROJECT_ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "report": args.report.as_posix(),
        "case_count": report["dataset"]["case_count"],
        "event_metrics": report["event_metrics"],
        "older_adl_false_alarm_analysis": report["older_adl_false_alarm_analysis"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
