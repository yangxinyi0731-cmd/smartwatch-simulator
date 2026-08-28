from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.app.models.fall import FallModelAdapter
from backend.app.models.fall_evaluation import make_windows, merge_alarm_windows


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    PROJECT_ROOT / "models" / "fall_detector" / "tcn_final_candidate" / "manifest.json"
)


def test_committed_fall_model_loads_with_fixed_cpu_contract() -> None:
    adapter = FallModelAdapter(project_root=PROJECT_ROOT, manifest_path=MANIFEST_PATH)
    assert adapter.manifest.deployment_approved is False
    assert adapter.threshold == 0.7
    probabilities = adapter.predict_fall_probability(
        np.zeros((2, 200, 6), dtype=np.float32)
    )
    assert probabilities.shape == (2,)
    assert np.isfinite(probabilities).all()
    assert np.all((probabilities >= 0) & (probabilities <= 1))


def test_fall_adapter_rejects_wrong_or_nonfinite_input() -> None:
    adapter = FallModelAdapter(project_root=PROJECT_ROOT, manifest_path=MANIFEST_PATH)
    with pytest.raises(ValueError, match="200, 6"):
        adapter.predict_fall_probability(np.zeros((1, 200, 3), dtype=np.float32))
    invalid = np.zeros((1, 200, 6), dtype=np.float32)
    invalid[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        adapter.predict_fall_probability(invalid)


def test_windowing_and_episode_merging_are_deterministic() -> None:
    windows, starts = make_windows(np.zeros((350, 6), dtype=np.float32))
    assert windows.shape == (4, 200, 6)
    assert starts == (0, 50, 100, 150)
    episodes = merge_alarm_windows(starts, (0.2, 0.8, 0.9, 0.1), 0.7)
    assert len(episodes) == 1
    assert episodes[0].start_offset_ms == 1000
    assert episodes[0].end_offset_ms == 6000
    assert episodes[0].peak_probability == pytest.approx(0.9)
    assert episodes[0].window_count == 2
