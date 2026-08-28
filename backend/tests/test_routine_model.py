from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.app.contracts import RoutineEventContract, TruthCategory
from backend.scripts.build_routine_model import PROFILE_ID, generate_events, learn_rules


def test_synthetic_routine_generation_is_deterministic_and_truth_labeled() -> None:
    first = generate_events()
    second = generate_events()
    assert first == second
    assert len(first) > 300
    assert {event.event_type for event in first} == {"meal", "nap", "walk"}
    assert len({event.started_at.date() for event in first}) == 100
    assert all(event.truth_category.value == "SYNTHETIC_ROUTINE" for event in first)


def test_routine_rules_cover_three_independent_event_types() -> None:
    artifact = learn_rules(generate_events(), "a" * 40)
    assert artifact.history_days == 100
    assert tuple(rule.event_type for rule in artifact.rules) == ("meal", "nap", "walk")
    assert all(rule.slots for rule in artifact.rules)


def test_routine_event_contract_rejects_real_truth_category() -> None:
    with pytest.raises(ValidationError):
        RoutineEventContract(
            event_id="fixture",
            profile_id=PROFILE_ID,
            event_type="meal",
            slot_key="breakfast",
            started_at=datetime(2026, 1, 1, 8, tzinfo=timezone(timedelta(hours=8))),
            duration_minutes=30,
            truth_category=TruthCategory.REAL_FREE_LIVING,
        )
