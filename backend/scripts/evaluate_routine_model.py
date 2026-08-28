from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, time
from pathlib import Path

from backend.app.contracts import RoutineEventContract
from backend.app.models.routine import RoutineModelAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVENTS = Path("data/cases/synthetic_routine_100_v1.json")
DEFAULT_MANIFEST = Path("models/routine_anomaly/statistical_v1/manifest.json")
DEFAULT_REPORT = Path("reports/models/routine_anomaly_scenarios.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _status_map(adapter: RoutineModelAdapter, events: tuple[RoutineEventContract, ...]) -> dict[str, str]:
    return {item.event_type: item.status for item in adapter.assess_day(events)}


def evaluate(events_path: Path, manifest_path: Path) -> dict[str, object]:
    events_payload = json.loads(events_path.read_text(encoding="utf-8"))
    all_events = tuple(
        RoutineEventContract.model_validate(item) for item in events_payload["events"]
    )
    adapter = RoutineModelAdapter(project_root=PROJECT_ROOT, manifest_path=manifest_path)
    by_day: dict[object, list[RoutineEventContract]] = defaultdict(list)
    for event in all_events:
        by_day[event.started_at.date()].append(event)
    baseline: tuple[RoutineEventContract, ...] | None = None
    for day_events in by_day.values():
        candidate = tuple(day_events)
        statuses = _status_map(adapter, candidate)
        if statuses == {"meal": "WITHIN_ROUTINE", "nap": "WITHIN_ROUTINE", "walk": "WITHIN_ROUTINE"} and any(
            item.event_type == "nap" for item in candidate
        ):
            baseline = candidate
            break
    if baseline is None:
        raise RuntimeError("没有找到可用于规则场景核验的完整基线日。")

    late_events = tuple(
        event.model_copy(
            update={
                "started_at": datetime.combine(
                    event.started_at.date(),
                    time(23, 30),
                    tzinfo=event.started_at.tzinfo,
                )
            }
        )
        if event.event_type == "meal" and event.slot_key == "dinner"
        else event
        for event in baseline
    )
    missing_meals = tuple(event for event in baseline if event.event_type != "meal")
    walk_rule = next(rule for rule in adapter.artifact.rules if rule.event_type == "walk")
    extra_walks = list(baseline)
    walk_template = next(event for event in baseline if event.event_type == "walk")
    current_walk_count = sum(event.event_type == "walk" for event in baseline)
    for index in range(current_walk_count + 1, walk_rule.daily_count_max + 2):
        extra_walks.append(
            walk_template.model_copy(
                update={
                    "event_id": f"scenario-extra-walk-{index}",
                    "slot_key": f"walk_extra_{index}",
                    "started_at": walk_template.started_at.replace(hour=min(22, 17 + index)),
                }
            )
        )
    nap_rule = next(rule for rule in adapter.artifact.rules if rule.event_type == "nap")
    nap_max = nap_rule.slots[0].duration_interval_max_minutes
    long_nap = tuple(
        event.model_copy(update={"duration_minutes": nap_max + 30})
        if event.event_type == "nap"
        else event
        for event in baseline
    )
    scenarios = (
        ("baseline_day", baseline, {"meal": "WITHIN_ROUTINE", "nap": "WITHIN_ROUTINE", "walk": "WITHIN_ROUTINE"}),
        ("late_dinner", late_events, {"meal": "LATE"}),
        ("missing_meals", missing_meals, {"meal": "MISSING"}),
        ("extra_walk", tuple(extra_walks), {"walk": "COUNT_DEVIATION"}),
        ("long_nap", long_nap, {"nap": "DURATION_DEVIATION"}),
    )
    results: list[dict[str, object]] = []
    for scenario_id, events, expected in scenarios:
        assessments = adapter.assess_day(events)
        actual = {item.event_type: item.status for item in assessments}
        passed = all(actual[key] == value for key, value in expected.items())
        results.append(
            {
                "scenario_id": scenario_id,
                "expected_statuses": expected,
                "actual_statuses": actual,
                "passed": passed,
                "assessments": [item.model_dump(mode="json") for item in assessments],
            }
        )
    return {
        "report_version": "1.0.0",
        "execution_command": (
            "python -m backend.scripts.evaluate_routine_model "
            "--events data/cases/synthetic_routine_100_v1.json "
            "--manifest models/routine_anomaly/statistical_v1/manifest.json "
            "--report reports/models/routine_anomaly_scenarios.json"
        ),
        "model": {
            "manifest_id": adapter.manifest.manifest_id,
            "artifact_sha256": adapter.manifest.artifact_sha256,
            "deployment_approved": adapter.manifest.deployment_approved,
        },
        "history": {
            "truth_category": events_payload["truth_category"],
            "history_days": events_payload["history_days"],
            "event_count": events_payload["event_count"],
            "events_sha256": _sha256(events_path),
            "seed": events_payload["seed"],
        },
        "scenario_count": len(results),
        "passed_scenario_count": sum(bool(item["passed"]) for item in results),
        "scenarios": results,
        "meaning": (
            "这些场景只核验确定性规则的预期分支，不是从真实老人数据计算的准确率、"
            "召回率或医学风险。"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="核验合成生活规律规则的确定性场景。")
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = evaluate(
        PROJECT_ROOT / args.events,
        PROJECT_ROOT / args.manifest,
    )
    report_path = PROJECT_ROOT / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "report": args.report.as_posix(),
                "scenario_count": report["scenario_count"],
                "passed_scenario_count": report["passed_scenario_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
