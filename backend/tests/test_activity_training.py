from __future__ import annotations

from pathlib import Path

import numpy as np
import onnxruntime as ort
import pytest

from backend.app.training.activity import (
    LABELS,
    SOURCE_WINDOW_SAMPLES,
    TARGET_WINDOW_SAMPLES,
    build_onnx,
    downsample_window,
    extract_features,
    map_annotation,
    predict_softmax,
    train_softmax,
)


def test_annotation_mapping_is_explicit_and_conservative() -> None:
    assert map_annotation("leisure;walking;17150 walking outdoors") == "walking"
    assert map_annotation("leisure;eating;13030 eating sitting") == "eating_candidate"
    assert map_annotation("Sleeping") == "sleep_or_lying_candidate"
    assert map_annotation("Typing at a desk") == "other_unknown"
    assert (
        map_annotation("office work such as typing (with or without eating at the same time)")
        == "other_unknown"
    )
    assert map_annotation("") is None


def test_downsample_uses_real_three_axis_values_and_converts_units() -> None:
    source = np.ones((SOURCE_WINDOW_SAMPLES, 3), dtype=np.float32)
    reduced = downsample_window(source)
    assert reduced.shape == (TARGET_WINDOW_SAMPLES, 3)
    assert np.allclose(reduced, 9.80665)


def test_numpy_training_and_onnx_export_are_numerically_consistent(tmp_path: Path) -> None:
    rng = np.random.default_rng(7)
    windows = []
    labels = []
    for label_index in range(len(LABELS)):
        base = np.zeros((24, TARGET_WINDOW_SAMPLES, 3), dtype=np.float32)
        base[:, :, label_index % 3] = label_index + 1
        base += rng.normal(0, 0.03, size=base.shape).astype(np.float32)
        windows.append(base)
        labels.extend([label_index] * len(base))
    values = np.concatenate(windows)
    target = np.asarray(labels, dtype=np.int64)
    assert extract_features(values).shape == (len(values), 11)
    model = train_softmax(values, target, iterations=300)
    path = tmp_path / "activity.onnx"
    build_onnx(model, path)
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    runtime = session.run(
        ["activity_probabilities"],
        {"acceleration_window": values},
    )[0]
    expected = predict_softmax(model, values)
    assert np.max(np.abs(runtime - expected)) < 1e-5
    assert np.allclose(runtime.sum(axis=1), 1.0, atol=1e-5)


def test_activity_features_reject_wrong_shape() -> None:
    with pytest.raises(ValueError, match="400, 3"):
        extract_features(np.zeros((2, 200, 3), dtype=np.float32))
