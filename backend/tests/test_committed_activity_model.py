from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from backend.app.models.activity import ActivityModelAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIRECTORY = (
    PROJECT_ROOT / "models" / "activity_recognition" / "capture24_linear_v1"
)
MANIFEST_PATH = MODEL_DIRECTORY / "manifest.json"
REPORT_PATH = PROJECT_ROOT / "reports" / "models" / "activity_capture24_group_holdout.json"
CATALOG_PATH = PROJECT_ROOT / "data" / "catalog" / "capture24_activity_training_v1.json"


def test_committed_activity_artifact_and_manifest_are_runtime_compatible() -> None:
    adapter = ActivityModelAdapter(
        project_root=PROJECT_ROOT,
        manifest_path=MANIFEST_PATH,
    )
    manifest = adapter.manifest
    artifact = PROJECT_ROOT / str(manifest.artifact_relative_path)
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == manifest.artifact_sha256
    assert manifest.deployment_approved is False
    assert manifest.external_validation_completed is False
    probabilities = adapter.predict_probabilities(
        np.zeros((1, 400, 3), dtype=np.float32)
    )
    assert probabilities.shape == (1, 4)
    assert np.isclose(probabilities.sum(), 1.0)


def test_committed_activity_report_preserves_split_metrics_and_subset_scope() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    metrics = report["evaluation"]["participant_group_holdout_metrics"]
    matrix = np.asarray(metrics["confusion_matrix"], dtype=np.int64)
    training = set(report["split"]["training_participants"])
    evaluation = set(report["split"]["evaluation_participants"])

    assert matrix.shape == (4, 4)
    assert int(matrix.sum()) == report["evaluation"]["window_count"] == 3728
    assert np.isclose(np.trace(matrix) / matrix.sum(), metrics["accuracy"])
    assert len(training) == 24
    assert len(evaluation) == 12
    assert training.isdisjoint(evaluation)
    assert report["split"]["overlap"] == []
    assert catalog["source_archive_scope"] == "recovered_official_prefix_subset"
    assert catalog["source_recovery_catalog"]["participant_count"] == 48
    assert report["onnx"]["max_abs_error_vs_numpy"] < 1e-5
    assert any("不是完整 151 人" in item for item in report["limitations"])
