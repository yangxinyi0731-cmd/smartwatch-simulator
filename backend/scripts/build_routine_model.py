from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path

import numpy as np

from backend.app.contracts import (
    ApprovalStatus,
    ManifestFormat,
    ModelKind,
    ModelManifest,
    RoutineEventContract,
    TruthCategory,
    model_contracts,
)
from backend.app.models.routine import (
    RoutineRulesArtifact,
    RoutineSlotRule,
    RoutineTypeRule,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXPECTED_ARCHIVE_SHA256 = "dedd7d85dbaa982389bfa7fbed22cd24a616deeb6ad7fab329cae5d3222dfd1b"
PROFILE_ID = "synthetic-routine-100-v1"
SEED = 20260828
HISTORY_START = date(2026, 1, 1)
CHINA_TZ = timezone(timedelta(hours=8))
EVENTS_PATH = Path("data/cases/synthetic_routine_100_v1.json")
RULES_PATH = Path("models/routine_anomaly/statistical_v1/rules.json")
MANIFEST_PATH = Path("models/routine_anomaly/statistical_v1/manifest.json")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _started_at(day: date, hour: float) -> datetime:
    seconds = int(round(hour * 3600))
    return datetime.combine(day, time(), tzinfo=CHINA_TZ) + timedelta(seconds=seconds)


def generate_events() -> tuple[RoutineEventContract, ...]:
    rng = np.random.default_rng(SEED)
    events: list[RoutineEventContract] = []
    sequence = 0

    def append(
        day_index: int,
        event_type: str,
        slot_key: str,
        hour: float,
        duration: float,
    ) -> None:
        nonlocal sequence
        sequence += 1
        events.append(
            RoutineEventContract(
                event_id=f"routine-{sequence:04d}",
                profile_id=PROFILE_ID,
                event_type=event_type,
                slot_key=slot_key,
                started_at=_started_at(HISTORY_START + timedelta(days=day_index), hour),
                duration_minutes=float(duration),
            )
        )

    for day_index in range(100):
        meal_count = int(rng.choice([2, 3], p=[0.1, 0.9]))
        meal_slots = (
            ["breakfast", "dinner"]
            if meal_count == 2 and rng.random() < 0.7
            else ["lunch", "dinner"]
            if meal_count == 2
            else ["breakfast", "lunch", "dinner"]
        )
        meal_base = {"breakfast": 7.5, "lunch": 12.5, "dinner": 18.5}
        meal_duration = {"breakfast": 25, "lunch": 35, "dinner": 40}
        for slot in meal_slots:
            append(
                day_index,
                "meal",
                slot,
                float(np.clip(meal_base[slot] + rng.normal(0, 0.4), 5, 22)),
                float(np.clip(meal_duration[slot] + rng.normal(0, 8), 10, 90)),
            )

        if rng.random() < 0.7:
            append(
                day_index,
                "nap",
                "nap",
                float(np.clip(rng.uniform(12, 14.5) + rng.normal(0, 0.3), 11, 15.5)),
                float(np.clip(rng.normal(45, 15), 15, 90)),
            )

        walk_count = int(rng.choice([1, 2, 3], p=[0.2, 0.5, 0.3]))
        walk_bases = {1: [9.5], 2: [9.0, 16.5], 3: [8.5, 12.5, 17.0]}[walk_count]
        for index, base in enumerate(walk_bases, start=1):
            append(
                day_index,
                "walk",
                f"walk_{index}",
                float(np.clip(base + rng.normal(0, 0.5), 6, 22)),
                float(np.clip(rng.normal(30, 10), 10, 90)),
            )
    return tuple(events)


def _robust_interval(values: list[float], multiplier: float) -> tuple[float, float, float, float]:
    array = np.asarray(values, dtype=np.float64)
    q1, q3 = np.quantile(array, (0.25, 0.75))
    iqr = q3 - q1
    filtered = array[(array >= q1 - 1.5 * iqr) & (array <= q3 + 1.5 * iqr)]
    if len(filtered) < 3:
        filtered = array
    mean = float(np.mean(filtered))
    std = float(np.std(filtered))
    return mean, std, mean - multiplier * std, mean + multiplier * std


def learn_rules(events: tuple[RoutineEventContract, ...], source_commit: str) -> RoutineRulesArtifact:
    by_type_and_slot: dict[tuple[str, str], list[RoutineEventContract]] = defaultdict(list)
    daily_counts: dict[str, Counter[date]] = {
        "meal": Counter(),
        "nap": Counter(),
        "walk": Counter(),
    }
    for event in events:
        by_type_and_slot[(event.event_type, event.slot_key)].append(event)
        daily_counts[event.event_type][event.started_at.date()] += 1
    multiplier = 2.0
    type_rules: list[RoutineTypeRule] = []
    for event_type in ("meal", "nap", "walk"):
        slots: list[RoutineSlotRule] = []
        for (_, slot_key), selected in sorted(by_type_and_slot.items()):
            if selected[0].event_type != event_type:
                continue
            hours = [
                item.started_at.hour
                + item.started_at.minute / 60
                + item.started_at.second / 3600
                for item in selected
            ]
            durations = [item.duration_minutes for item in selected]
            start_mean, start_std, start_min, start_max = _robust_interval(hours, multiplier)
            duration_mean, duration_std, duration_min, duration_max = _robust_interval(
                durations, multiplier
            )
            slots.append(
                RoutineSlotRule(
                    slot_key=slot_key,
                    sample_count=len(selected),
                    start_mean_hour=start_mean,
                    start_std_hour=start_std,
                    start_interval_min_hour=max(0.0, start_min),
                    start_interval_max_hour=min(24.0, start_max),
                    duration_mean_minutes=duration_mean,
                    duration_std_minutes=duration_std,
                    duration_interval_min_minutes=max(0.1, duration_min),
                    duration_interval_max_minutes=duration_max,
                )
            )
        counts = [daily_counts[event_type][HISTORY_START + timedelta(days=index)] for index in range(100)]
        type_rules.append(
            RoutineTypeRule(
                event_type=event_type,
                daily_count_min=min(counts),
                daily_count_max=max(counts),
                slots=tuple(slots),
            )
        )
    return RoutineRulesArtifact(
        profile_id=PROFILE_ID,
        seed=SEED,
        generator_source_commit=source_commit,
        source_archive_sha256=EXPECTED_ARCHIVE_SHA256,
        source_archive_note=(
            "本机用户提供的 anomaly_detection(1).zip 仅作需求与思路核验；"
            "未复制其中代码，规则由本项目独立、确定性实现。"
        ),
        std_multiplier=multiplier,
        rules=tuple(type_rules),
    )


def _write_json(path: Path, payload: object) -> str:
    path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != serialized:
        raise ValueError(f"现有生成物与确定性结果冲突：{path}")
    path.write_text(serialized, encoding="utf-8")
    return _sha256(path)


def build(source_archive: Path, source_commit: str) -> ModelManifest:
    source_archive = source_archive.resolve()
    if _sha256(source_archive) != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("规律异常来源压缩包 SHA-256 与固定记录不一致。")
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
    events = generate_events()
    events_payload = {
        "format_version": "1.0.0",
        "profile_id": PROFILE_ID,
        "truth_category": TruthCategory.SYNTHETIC_ROUTINE.value,
        "history_start": HISTORY_START.isoformat(),
        "history_days": 100,
        "seed": SEED,
        "event_count": len(events),
        "events": [event.model_dump(mode="json") for event in events],
    }
    events_hash = _write_json(EVENTS_PATH, events_payload)
    rules = learn_rules(events, source_commit)
    rules_hash = _write_json(RULES_PATH, rules.model_dump(mode="json"))
    contract = next(
        item for item in model_contracts() if item.model_kind is ModelKind.ROUTINE_ANOMALY
    )
    manifest = ModelManifest(
        manifest_id="routine-anomaly-statistical-1.0.0",
        model_id="routine_anomaly_statistical_rules",
        model_kind=ModelKind.ROUTINE_ANOMALY,
        version="1.0.0",
        format=ManifestFormat.STATISTICAL_RULES,
        source_commit=source_commit,
        artifact_relative_path=RULES_PATH.as_posix(),
        artifact_sha256=rules_hash,
        contract=contract,
        training_truth_categories=(TruthCategory.SYNTHETIC_ROUTINE,),
        training_data_references=(
            f"{EVENTS_PATH.as_posix()} sha256={events_hash}",
            f"local source archive sha256={EXPECTED_ARCHIVE_SHA256}",
        ),
        evaluation_reference="reports/models/routine_anomaly_scenarios.json",
        limitations=(
            "训练历史是固定种子生成的 100 天合成生活事件，不是真实老人记录。",
            "规则只覆盖用餐、午睡和散步的时间、次数与时长。",
            "异常分数是规则距离的 0–1 归一化，不是医学风险概率。",
            "尚未用真实长期生活数据做外部验证。",
        ),
        deployment_approved=False,
        approval_status=ApprovalStatus.RESEARCH_ONLY,
        external_validation_completed=False,
        created_at=committed_at,
    )
    _write_json(MANIFEST_PATH, manifest.model_dump(mode="json"))
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 100 天合成生活规律与统计规则。")
    parser.add_argument("--source-archive", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build(args.source_archive, args.source_commit)
    print(manifest.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
