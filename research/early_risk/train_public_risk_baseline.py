from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from research.early_risk.common import PROJECT_ROOT, sha256_file
from research.early_risk.public_risk_model import (
    CONTEXT_SAMPLES,
    CONTEXT_SECONDS,
    HORIZONS_SECONDS,
    MODEL_SAMPLE_RATE_HZ,
    MODEL_SCHEMA_VERSION,
    PublicEarlyRiskModel,
    extract_features,
)


CATALOG_PATH = PROJECT_ROOT / "data" / "catalog" / "weda_fall_100_v1.json"
ARTIFACT_PATH = (
    PROJECT_ROOT / "models" / "early_risk" / "public_weda_linear_v1" / "model.json"
)
MANIFEST_PATH = ARTIFACT_PATH.with_name("manifest.json")
REPORT_PATH = PROJECT_ROOT / "reports" / "early_risk" / "public_weda_linear_v1.json"
TRAIN_PARTICIPANTS = ("U03", "U04", "U07", "U09", "U11", "U12", "U13") + tuple(
    f"U{index:02d}" for index in range(21, 27)
)
CALIBRATION_PARTICIPANTS = ("U02", "U06", "U10", "U27")
# The fixed evaluation group deliberately contains enough long pre-anchor records
# to make the exact 3-second snapshot denominator visible, while remaining fully
# participant-disjoint from model fitting and threshold calibration.
EVALUATION_PARTICIPANTS = ("U01", "U05", "U08", "U14") + tuple(
    f"U{index:02d}" for index in range(28, 32)
)
STRIDE_SAMPLES = 10
MAX_ADL_WINDOWS_PER_CASE = 60


@dataclass(frozen=True)
class Example:
    case_id: str
    participant_id: str
    truth_category: str
    end_sample: int
    anchor_sample: int | None
    features: np.ndarray

    def label(self, horizon_seconds: int) -> int:
        if self.anchor_sample is None:
            return 0
        lead_samples = self.anchor_sample - self.end_sample
        return int(0 < lead_samples <= horizon_seconds * MODEL_SAMPLE_RATE_HZ)


def _load_catalog(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("case_count") != len(payload.get("cases", [])):
        raise ValueError("WEDA 目录案例数不一致。")
    return payload


def _fall_anchor_sample(entry: dict[str, Any]) -> int | None:
    events = [
        event
        for event in entry["ground_truth_events"]
        if event["event_type"] == "FALL_INTERVAL"
    ]
    if not events:
        return None
    if len(events) != 1:
        raise ValueError("每个受控跌倒案例必须只有一个 FALL_INTERVAL。")
    return int(round(float(events[0]["start_offset_ms"]) * MODEL_SAMPLE_RATE_HZ / 1000))


def _candidate_end_samples(sample_count: int, anchor_sample: int | None) -> list[int]:
    last_end = sample_count if anchor_sample is None else min(sample_count, anchor_sample - 1)
    if last_end < CONTEXT_SAMPLES:
        return []
    ends = list(range(CONTEXT_SAMPLES, last_end + 1, STRIDE_SAMPLES))
    if ends[-1] != last_end:
        ends.append(last_end)
    if anchor_sample is not None:
        for horizon in HORIZONS_SECONDS:
            special_end = anchor_sample - int(horizon * MODEL_SAMPLE_RATE_HZ)
            if CONTEXT_SAMPLES <= special_end <= last_end:
                ends.append(special_end)
    ends = sorted(set(ends))
    if anchor_sample is None and len(ends) > MAX_ADL_WINDOWS_PER_CASE:
        indices = np.linspace(0, len(ends) - 1, MAX_ADL_WINDOWS_PER_CASE, dtype=int)
        ends = [ends[index] for index in indices]
    return ends


def build_examples(catalog_path: Path = CATALOG_PATH) -> tuple[tuple[str, ...], list[Example]]:
    payload = _load_catalog(catalog_path)
    feature_names: tuple[str, ...] | None = None
    examples: list[Example] = []
    for entry in payload["cases"]:
        case = entry["case"]
        stream = entry["stream"]
        if stream["channels"] != ["ax", "ay", "az", "gx", "gy", "gz"]:
            raise ValueError("WEDA 提前风险训练只接受标准六轴顺序。")
        if float(stream["sample_rate_hz"]) != MODEL_SAMPLE_RATE_HZ:
            raise ValueError("WEDA 提前风险训练只接受 50 Hz 输入。")
        path = (PROJECT_ROOT / stream["relative_path"]).resolve()
        if PROJECT_ROOT not in path.parents or not path.is_file():
            raise FileNotFoundError(f"训练文件不存在：{case['case_id']}")
        if sha256_file(path) != stream["content_sha256"]:
            raise ValueError(f"训练文件哈希不一致：{case['case_id']}")
        values = np.load(path, allow_pickle=False)
        if values.shape != (int(stream["sample_count"]), 6):
            raise ValueError(f"训练文件形状不一致：{case['case_id']}")
        anchor_sample = _fall_anchor_sample(entry)
        for end_sample in _candidate_end_samples(len(values), anchor_sample):
            names, features = extract_features(values[end_sample - CONTEXT_SAMPLES : end_sample])
            if feature_names is None:
                feature_names = names
            elif names != feature_names:
                raise RuntimeError("特征顺序不稳定。")
            examples.append(
                Example(
                    case_id=str(case["case_id"]),
                    participant_id=str(case["participant_id"]),
                    truth_category=str(case["truth_category"]),
                    end_sample=end_sample,
                    anchor_sample=anchor_sample,
                    features=features,
                )
            )
    if feature_names is None or not examples:
        raise ValueError("没有生成提前风险训练样本。")
    return feature_names, examples


def _matrix(examples: list[Example], participants: tuple[str, ...]) -> tuple[np.ndarray, list[Example]]:
    selected = [item for item in examples if item.participant_id in participants]
    if not selected:
        raise ValueError("参与者划分没有样本。")
    return np.vstack([item.features for item in selected]), selected


def _sigmoid(logits: np.ndarray) -> np.ndarray:
    clipped = np.clip(logits, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _fit_logistic(features: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, float]:
    positives = int(np.sum(labels == 1))
    negatives = int(np.sum(labels == 0))
    if positives == 0 or negatives == 0:
        raise ValueError("每个提前时间都必须同时包含正例和负例。")
    sample_weights = np.where(labels == 1, 0.5 / positives, 0.5 / negatives) * len(labels)
    weights = np.zeros(features.shape[1], dtype=np.float64)
    bias = 0.0
    first_moment_w = np.zeros_like(weights)
    second_moment_w = np.zeros_like(weights)
    first_moment_b = 0.0
    second_moment_b = 0.0
    beta1 = 0.9
    beta2 = 0.999
    learning_rate = 0.025
    l2 = 0.004
    for step in range(1, 1801):
        probabilities = _sigmoid(features @ weights + bias)
        residual = (probabilities - labels) * sample_weights
        gradient_w = features.T @ residual / len(labels) + l2 * weights
        gradient_b = float(np.sum(residual) / len(labels))
        first_moment_w = beta1 * first_moment_w + (1 - beta1) * gradient_w
        second_moment_w = beta2 * second_moment_w + (1 - beta2) * np.square(gradient_w)
        first_moment_b = beta1 * first_moment_b + (1 - beta1) * gradient_b
        second_moment_b = beta2 * second_moment_b + (1 - beta2) * gradient_b * gradient_b
        corrected_w = first_moment_w / (1 - beta1**step)
        corrected_w2 = second_moment_w / (1 - beta2**step)
        corrected_b = first_moment_b / (1 - beta1**step)
        corrected_b2 = second_moment_b / (1 - beta2**step)
        weights -= learning_rate * corrected_w / (np.sqrt(corrected_w2) + 1e-8)
        bias -= learning_rate * corrected_b / (np.sqrt(corrected_b2) + 1e-8)
    return weights, bias


def _confusion(labels: np.ndarray, predictions: np.ndarray) -> dict[str, int]:
    return {
        "true_positive": int(np.sum((labels == 1) & (predictions == 1))),
        "false_positive": int(np.sum((labels == 0) & (predictions == 1))),
        "true_negative": int(np.sum((labels == 0) & (predictions == 0))),
        "false_negative": int(np.sum((labels == 1) & (predictions == 0))),
    }


def _metrics(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(np.int64)
    matrix = _confusion(labels, predictions)
    tp = matrix["true_positive"]
    fp = matrix["false_positive"]
    fn = matrix["false_negative"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    order = np.argsort(-probabilities, kind="stable")
    sorted_labels = labels[order]
    cumulative_tp = np.cumsum(sorted_labels)
    cumulative_fp = np.cumsum(1 - sorted_labels)
    total_positive = max(1, int(np.sum(labels)))
    precisions = cumulative_tp / np.maximum(1, cumulative_tp + cumulative_fp)
    recalls = cumulative_tp / total_positive
    previous_recall = np.concatenate(([0.0], recalls[:-1]))
    average_precision = float(np.sum((recalls - previous_recall) * precisions))
    bins: list[dict[str, float | int]] = []
    ece = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (probabilities >= lower) & (
            probabilities <= upper if upper >= 1.0 else probabilities < upper
        )
        count = int(np.sum(mask))
        if not count:
            continue
        confidence = float(np.mean(probabilities[mask]))
        observed = float(np.mean(labels[mask]))
        ece += count / len(labels) * abs(confidence - observed)
        bins.append({"lower": round(float(lower), 2), "upper": round(float(upper), 2), "count": count, "mean_score": confidence, "observed_rate": observed})
    return {
        "sample_count": len(labels),
        "positive_count": int(np.sum(labels)),
        "negative_count": int(np.sum(labels == 0)),
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "average_precision": average_precision,
        "brier_score": float(np.mean(np.square(probabilities - labels))),
        "expected_calibration_error_10_bins": float(ece),
        "confusion": matrix,
        "calibration_bins": bins,
    }


def _choose_threshold(labels: np.ndarray, probabilities: np.ndarray) -> float:
    best: tuple[float, float, float] | None = None
    for threshold in np.linspace(0.20, 0.80, 121):
        metrics = _metrics(labels, probabilities, float(threshold))
        candidate = (float(metrics["f1"]), float(metrics["precision"]), -float(threshold))
        if best is None or candidate > best:
            best = candidate
    assert best is not None
    return -best[2]


def _snapshot_metrics(
    examples: list[Example], probabilities: np.ndarray, thresholds: np.ndarray
) -> dict[str, Any]:
    by_case: dict[str, list[tuple[Example, np.ndarray]]] = {}
    for example, row in zip(examples, probabilities, strict=True):
        if example.anchor_sample is not None:
            by_case.setdefault(example.case_id, []).append((example, row))
    result: dict[str, Any] = {}
    for head_index, horizon in enumerate(HORIZONS_SECONDS):
        target_lead = int(horizon * MODEL_SAMPLE_RATE_HZ)
        eligible = []
        detected = 0
        scores: list[float] = []
        for case_id, rows in sorted(by_case.items()):
            exact = [
                (example, score)
                for example, score in rows
                if example.anchor_sample - example.end_sample == target_lead
            ]
            if not exact:
                continue
            example, score_row = exact[0]
            score = float(score_row[head_index])
            eligible.append(case_id)
            scores.append(score)
            detected += int(score >= thresholds[head_index])
        result[str(horizon)] = {
            "requested_lead_seconds": horizon,
            "eligible_simulated_fall_count": len(eligible),
            "detected_at_or_above_threshold": detected,
            "recall": detected / len(eligible) if eligible else None,
            "mean_score": float(np.mean(scores)) if scores else None,
            "case_ids": eligible,
            "definition": "仅使用截至代理锚点前恰好该秒数的 1 秒窗口。",
        }
    return result


def _case_counts(examples: list[Example]) -> dict[str, Any]:
    case_ids = sorted({item.case_id for item in examples})
    fall_ids = sorted({item.case_id for item in examples if item.anchor_sample is not None})
    return {
        "window_count": len(examples),
        "case_count": len(case_ids),
        "simulated_fall_case_count": len(fall_ids),
        "adl_case_count": len(case_ids) - len(fall_ids),
        "participant_count": len({item.participant_id for item in examples}),
    }


def train(
    *,
    catalog_path: Path = CATALOG_PATH,
    artifact_path: Path = ARTIFACT_PATH,
    manifest_path: Path = MANIFEST_PATH,
    report_path: Path = REPORT_PATH,
) -> dict[str, Any]:
    feature_names, examples = build_examples(catalog_path)
    train_x, train_examples = _matrix(examples, TRAIN_PARTICIPANTS)
    calibration_x, calibration_examples = _matrix(examples, CALIBRATION_PARTICIPANTS)
    evaluation_x, evaluation_examples = _matrix(examples, EVALUATION_PARTICIPANTS)
    split_sets = [set(TRAIN_PARTICIPANTS), set(CALIBRATION_PARTICIPANTS), set(EVALUATION_PARTICIPANTS)]
    if any(split_sets[left] & split_sets[right] for left in range(3) for right in range(left + 1, 3)):
        raise RuntimeError("参与者划分发生交叉。")

    mean = np.mean(train_x, axis=0)
    scale = np.std(train_x, axis=0)
    scale[scale < 1e-8] = 1.0
    train_z = (train_x - mean) / scale
    calibration_z = (calibration_x - mean) / scale
    evaluation_z = (evaluation_x - mean) / scale

    weights: list[np.ndarray] = []
    biases: list[float] = []
    calibration_raw: list[np.ndarray] = []
    evaluation_raw: list[np.ndarray] = []
    for horizon in HORIZONS_SECONDS:
        labels = np.asarray([item.label(horizon) for item in train_examples], dtype=np.float64)
        fitted_weights, fitted_bias = _fit_logistic(train_z, labels)
        weights.append(fitted_weights)
        biases.append(fitted_bias)
        calibration_raw.append(_sigmoid(calibration_z @ fitted_weights + fitted_bias))
        evaluation_raw.append(_sigmoid(evaluation_z @ fitted_weights + fitted_bias))

    calibration_probabilities = np.maximum.accumulate(np.column_stack(calibration_raw), axis=1)
    evaluation_probabilities = np.maximum.accumulate(np.column_stack(evaluation_raw), axis=1)
    thresholds = np.asarray(
        [
            _choose_threshold(
                np.asarray([item.label(horizon) for item in calibration_examples], dtype=np.int64),
                calibration_probabilities[:, index],
            )
            for index, horizon in enumerate(HORIZONS_SECONDS)
        ],
        dtype=np.float64,
    )

    artifact = {
        "schema_version": MODEL_SCHEMA_VERSION,
        "model_id": "public-weda-early-risk-linear-v1",
        "model_kind": "PUBLIC_PROXY_EARLY_RISK_RESEARCH",
        "created_at": datetime.now(UTC).isoformat(),
        "proxy_anchor": "WEDA_FALL_INTERVAL_START",
        "proxy_anchor_meaning": "固定数据集标注的受控跌倒区间开始；不是经专家判定的真实 t_instability。",
        "horizons_seconds": list(HORIZONS_SECONDS),
        "input_contract": {
            "sample_rate_hz": MODEL_SAMPLE_RATE_HZ,
            "context_seconds": CONTEXT_SECONDS,
            "sample_count": CONTEXT_SAMPLES,
            "channels": ["ax", "ay", "az", "gx", "gy", "gz"],
            "units": ["m/s^2", "m/s^2", "m/s^2", "rad/s", "rad/s", "rad/s"],
            "causal": True,
        },
        "feature_names": list(feature_names),
        "standardization": {"mean": mean.tolist(), "scale": scale.tolist()},
        "heads": {
            str(horizon): {
                "weights": weights[index].tolist(),
                "bias": biases[index],
                "threshold": float(thresholds[index]),
            }
            for index, horizon in enumerate(HORIZONS_SECONDS)
        },
        "output_contract": {
            "meaning": "与公开受控 WEDA 代理标签相匹配的研究分数，不是现实个人跌倒概率。",
            "monotonic_projection": "runtime enforces score_1s <= score_2s <= score_3s",
            "external_notification_allowed": False,
        },
        "limitations": [
            "正例来自参与者在床垫上的受控模拟跌倒，不是真实意外跌倒。",
            "时间锚点是数据集跌倒区间开始，不等同于真实失稳起点。",
            "模型没有使用自主采集数据，也没有外部数据集或真实手表验证。",
            "输出仅用于校赛研究演示，不能直接报警、诊断或联系救援。",
        ],
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifact_sha256 = sha256_file(artifact_path)

    manifest = {
        "manifest_id": "public-weda-early-risk-linear-1.0.0",
        "model_id": artifact["model_id"],
        "model_kind": artifact["model_kind"],
        "version": "1.0.0",
        "format": "portable_json_numpy_linear",
        "artifact_relative_path": artifact_path.relative_to(PROJECT_ROOT).as_posix(),
        "artifact_sha256": artifact_sha256,
        "training_catalog_relative_path": catalog_path.relative_to(PROJECT_ROOT).as_posix(),
        "training_catalog_sha256": sha256_file(catalog_path),
        "training_participants": list(TRAIN_PARTICIPANTS),
        "calibration_participants": list(CALIBRATION_PARTICIPANTS),
        "evaluation_participants": list(EVALUATION_PARTICIPANTS),
        "participant_disjoint": True,
        "self_collected_case_count": 0,
        "external_validation_completed": False,
        "deployment_approved": False,
        "proxy_anchor": artifact["proxy_anchor"],
        "limitations": artifact["limitations"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "report_version": "1.0.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "model": {
            "manifest_relative_path": manifest_path.relative_to(PROJECT_ROOT).as_posix(),
            "manifest_sha256": sha256_file(manifest_path),
            "artifact_relative_path": artifact_path.relative_to(PROJECT_ROOT).as_posix(),
            "artifact_sha256": artifact_sha256,
        },
        "research_question": "公开受控腕部六轴数据在代理锚点前 1、2、3 秒是否呈现可学习模式？",
        "proxy_anchor": {
            "code": artifact["proxy_anchor"],
            "meaning": artifact["proxy_anchor_meaning"],
            "is_adjudicated_t_instability": False,
        },
        "leakage_controls": {
            "causal_window": True,
            "post_anchor_samples_used": False,
            "participant_disjoint": True,
            "threshold_selected_on_evaluation": False,
        },
        "splits": {
            "training": {"participants": list(TRAIN_PARTICIPANTS), **_case_counts(train_examples)},
            "calibration": {"participants": list(CALIBRATION_PARTICIPANTS), **_case_counts(calibration_examples)},
            "evaluation": {"participants": list(EVALUATION_PARTICIPANTS), **_case_counts(evaluation_examples)},
        },
        "calibration_metrics": {
            str(horizon): _metrics(
                np.asarray([item.label(horizon) for item in calibration_examples], dtype=np.int64),
                calibration_probabilities[:, index],
                float(thresholds[index]),
            )
            for index, horizon in enumerate(HORIZONS_SECONDS)
        },
        "evaluation_metrics": {
            str(horizon): _metrics(
                np.asarray([item.label(horizon) for item in evaluation_examples], dtype=np.int64),
                evaluation_probabilities[:, index],
                float(thresholds[index]),
            )
            for index, horizon in enumerate(HORIZONS_SECONDS)
        },
        "evaluation_snapshot_at_exact_lead": _snapshot_metrics(
            evaluation_examples, evaluation_probabilities, thresholds
        ),
        "self_collected_engineering_validation": {
            "status": "AWAITING_REAL_FILES",
            "expected_case_count": 30,
            "received_case_count": 0,
            "claim_enabled": False,
        },
        "limitations": artifact["limitations"],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Reload and execute the saved artifact as a final portability gate.
    runtime = PublicEarlyRiskModel(artifact_path)
    smoke_values = np.stack(
        [
            np.zeros((CONTEXT_SAMPLES, 6), dtype=np.float64),
            np.ones((CONTEXT_SAMPLES, 6), dtype=np.float64),
        ]
    )
    smoke = runtime.predict_windows(smoke_values)
    if smoke.shape != (2, 3) or not np.isfinite(smoke).all():
        raise RuntimeError("保存后的提前风险模型运行核验失败。")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="训练公开 WEDA 代理锚点 1/2/3 秒研究基线。")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--artifact", type=Path, default=ARTIFACT_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    args = parser.parse_args()
    report = train(
        catalog_path=args.catalog.resolve(),
        artifact_path=args.artifact.resolve(),
        manifest_path=args.manifest.resolve(),
        report_path=args.report.resolve(),
    )
    digest = hashlib.sha256(json.dumps(report, sort_keys=True).encode("utf-8")).hexdigest()
    print(
        json.dumps(
            {
                "status": "PUBLIC_PROXY_BASELINE_READY",
                "report": str(args.report.resolve()),
                "report_content_digest": digest,
                "self_collected_received": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
