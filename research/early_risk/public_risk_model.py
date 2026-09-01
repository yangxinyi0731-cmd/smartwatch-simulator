from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


MODEL_SCHEMA_VERSION = "1.0.0"
MODEL_SAMPLE_RATE_HZ = 50.0
CONTEXT_SECONDS = 1.0
CONTEXT_SAMPLES = int(MODEL_SAMPLE_RATE_HZ * CONTEXT_SECONDS)
STEP_SAMPLES = 10
HORIZONS_SECONDS = (1, 2, 3)


def _safe_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if float(np.std(left)) < 1e-8 or float(np.std(right)) < 1e-8:
        return 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if np.isfinite(value) else 0.0


def _summary_features(prefix: str, values: np.ndarray) -> tuple[list[str], list[float]]:
    names = [
        f"{prefix}_mean",
        f"{prefix}_std",
        f"{prefix}_min",
        f"{prefix}_max",
        f"{prefix}_range",
        f"{prefix}_rms",
        f"{prefix}_p10",
        f"{prefix}_p50",
        f"{prefix}_p90",
    ]
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    features = [
        float(np.mean(values)),
        float(np.std(values)),
        minimum,
        maximum,
        maximum - minimum,
        float(np.sqrt(np.mean(np.square(values)))),
        float(np.quantile(values, 0.10)),
        float(np.quantile(values, 0.50)),
        float(np.quantile(values, 0.90)),
    ]
    return names, features


def extract_features(window: np.ndarray) -> tuple[tuple[str, ...], np.ndarray]:
    """Extract deterministic, causal features from one 1-second six-axis window."""

    values = np.asarray(window, dtype=np.float64)
    if values.shape != (CONTEXT_SAMPLES, 6):
        raise ValueError(f"提前风险窗口必须是 [{CONTEXT_SAMPLES}, 6]。")
    if not np.isfinite(values).all():
        raise ValueError("提前风险窗口不能包含 NaN 或无穷值。")

    names: list[str] = []
    features: list[float] = []
    for index, channel in enumerate(("ax", "ay", "az", "gx", "gy", "gz")):
        channel_names, channel_features = _summary_features(channel, values[:, index])
        names.extend(channel_names[:6])
        features.extend(channel_features[:6])

    acceleration = np.linalg.norm(values[:, :3], axis=1)
    angular_velocity = np.linalg.norm(values[:, 3:], axis=1)
    for prefix, signal in (("acc_mag", acceleration), ("gyro_mag", angular_velocity)):
        signal_names, signal_features = _summary_features(prefix, signal)
        names.extend(signal_names)
        features.extend(signal_features)

    acceleration_change = np.linalg.norm(np.diff(values[:, :3], axis=0), axis=1)
    angular_change = np.linalg.norm(np.diff(values[:, 3:], axis=0), axis=1)
    for prefix, signal in (("acc_change", acceleration_change), ("gyro_change", angular_change)):
        names.extend((f"{prefix}_mean", f"{prefix}_std", f"{prefix}_max", f"{prefix}_p90"))
        features.extend(
            (
                float(np.mean(signal)),
                float(np.std(signal)),
                float(np.max(signal)),
                float(np.quantile(signal, 0.90)),
            )
        )

    halfway = CONTEXT_SAMPLES // 2
    names.extend(("acc_mag_half_delta", "gyro_mag_half_delta"))
    features.extend(
        (
            float(np.mean(acceleration[halfway:]) - np.mean(acceleration[:halfway])),
            float(np.mean(angular_velocity[halfway:]) - np.mean(angular_velocity[:halfway])),
        )
    )
    for prefix, axes in (("acc", values[:, :3]), ("gyro", values[:, 3:])):
        for left, right, suffix in ((0, 1, "xy"), (0, 2, "xz"), (1, 2, "yz")):
            names.append(f"{prefix}_corr_{suffix}")
            features.append(_safe_correlation(axes[:, left], axes[:, right]))

    result = np.asarray(features, dtype=np.float64)
    if not np.isfinite(result).all():
        raise ValueError("提前风险特征计算产生了非有限数值。")
    return tuple(names), result


@dataclass(frozen=True)
class RiskPoint:
    offset_ms: int
    risk_1s: float
    risk_2s: float
    risk_3s: float
    attention_1s: bool
    attention_2s: bool
    attention_3s: bool


class PublicEarlyRiskModel:
    """Portable NumPy runtime for the public WEDA proxy-anchor research baseline."""

    def __init__(self, artifact_path: Path) -> None:
        self.artifact_path = artifact_path.resolve()
        payload = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != MODEL_SCHEMA_VERSION:
            raise ValueError("提前风险模型版本不受支持。")
        if payload.get("horizons_seconds") != list(HORIZONS_SECONDS):
            raise ValueError("提前风险模型必须包含 1、2、3 秒三个输出。")
        input_contract = payload.get("input_contract", {})
        if input_contract.get("sample_rate_hz") != MODEL_SAMPLE_RATE_HZ:
            raise ValueError("提前风险模型采样率合同必须是 50 Hz。")
        if input_contract.get("sample_count") != CONTEXT_SAMPLES:
            raise ValueError("提前风险模型窗口合同必须是 50 个样本。")

        self.model_id = str(payload["model_id"])
        self.proxy_anchor = str(payload["proxy_anchor"])
        self.feature_names = tuple(str(item) for item in payload["feature_names"])
        self.mean = np.asarray(payload["standardization"]["mean"], dtype=np.float64)
        self.scale = np.asarray(payload["standardization"]["scale"], dtype=np.float64)
        if self.mean.shape != self.scale.shape or self.mean.shape != (len(self.feature_names),):
            raise ValueError("提前风险模型标准化参数形状不一致。")
        if np.any(self.scale <= 0) or not np.isfinite(self.mean).all() or not np.isfinite(self.scale).all():
            raise ValueError("提前风险模型标准化参数无效。")

        heads = payload["heads"]
        self.weights = np.vstack(
            [np.asarray(heads[str(horizon)]["weights"], dtype=np.float64) for horizon in HORIZONS_SECONDS]
        )
        self.biases = np.asarray(
            [heads[str(horizon)]["bias"] for horizon in HORIZONS_SECONDS], dtype=np.float64
        )
        self.thresholds = np.asarray(
            [heads[str(horizon)]["threshold"] for horizon in HORIZONS_SECONDS], dtype=np.float64
        )
        if self.weights.shape != (len(HORIZONS_SECONDS), len(self.feature_names)):
            raise ValueError("提前风险模型权重形状不一致。")
        if np.any((self.thresholds <= 0) | (self.thresholds >= 1)):
            raise ValueError("提前风险模型阈值必须位于 0 到 1 之间。")

    def predict_feature_matrix(self, feature_matrix: np.ndarray) -> np.ndarray:
        values = np.asarray(feature_matrix, dtype=np.float64)
        if values.ndim != 2 or values.shape[1] != len(self.feature_names):
            raise ValueError("提前风险特征矩阵形状不符合模型合同。")
        standardized = (values - self.mean) / self.scale
        logits = standardized @ self.weights.T + self.biases
        logits = np.clip(logits, -40.0, 40.0)
        probabilities = 1.0 / (1.0 + np.exp(-logits))
        # A longer horizon contains the shorter horizon. This projection is part of
        # the saved runtime contract and prevents contradictory p1 > p2 > p3 output.
        return np.maximum.accumulate(probabilities, axis=1)

    def predict_windows(self, windows: np.ndarray) -> np.ndarray:
        values = np.asarray(windows, dtype=np.float64)
        if values.ndim != 3 or values.shape[1:] != (CONTEXT_SAMPLES, 6):
            raise ValueError(f"提前风险模型输入必须是 [batch, {CONTEXT_SAMPLES}, 6]。")
        if len(values) == 0:
            return np.empty((0, len(HORIZONS_SECONDS)), dtype=np.float64)
        matrix: list[np.ndarray] = []
        expected_names: tuple[str, ...] | None = None
        for window in values:
            names, features = extract_features(window)
            if expected_names is None:
                expected_names = names
            elif names != expected_names:
                raise RuntimeError("提前风险特征顺序发生变化。")
            matrix.append(features)
        if expected_names != self.feature_names:
            raise ValueError("运行时特征顺序与保存模型不一致。")
        return self.predict_feature_matrix(np.vstack(matrix))

    def predict_timeline(self, values: np.ndarray, *, step_samples: int = STEP_SAMPLES) -> tuple[RiskPoint, ...]:
        samples = np.asarray(values, dtype=np.float64)
        if samples.ndim != 2 or samples.shape[1] != 6:
            raise ValueError("提前风险时间线输入必须是 [samples, 6]。")
        if len(samples) < CONTEXT_SAMPLES:
            return ()
        if step_samples < 1:
            raise ValueError("时间线步长必须大于零。")
        ends = list(range(CONTEXT_SAMPLES, len(samples) + 1, step_samples))
        if ends[-1] != len(samples):
            ends.append(len(samples))
        windows = np.stack([samples[end - CONTEXT_SAMPLES : end] for end in ends])
        probabilities = self.predict_windows(windows)
        return tuple(
            RiskPoint(
                offset_ms=int(round(end * 1000 / MODEL_SAMPLE_RATE_HZ)),
                risk_1s=float(row[0]),
                risk_2s=float(row[1]),
                risk_3s=float(row[2]),
                attention_1s=bool(row[0] >= self.thresholds[0]),
                attention_2s=bool(row[1] >= self.thresholds[1]),
                attention_3s=bool(row[2] >= self.thresholds[2]),
            )
            for end, row in zip(ends, probabilities, strict=True)
        )


def risk_points_as_dicts(points: tuple[RiskPoint, ...]) -> list[dict[str, Any]]:
    return [
        {
            "offset_ms": point.offset_ms,
            "risk_1s": round(point.risk_1s, 6),
            "risk_2s": round(point.risk_2s, 6),
            "risk_3s": round(point.risk_3s, 6),
            "attention_1s": point.attention_1s,
            "attention_2s": point.attention_2s,
            "attention_3s": point.attention_3s,
        }
        for point in points
    ]
