from __future__ import annotations

import csv
import gzip
import io
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Sequence

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper


LABELS = (
    "walking",
    "eating_candidate",
    "sleep_or_lying_candidate",
    "other_unknown",
)
LABEL_TO_INDEX = {label: index for index, label in enumerate(LABELS)}
SOURCE_RATE_HZ = 100
TARGET_RATE_HZ = 20
WINDOW_SECONDS = 20
SOURCE_WINDOW_SAMPLES = SOURCE_RATE_HZ * WINDOW_SECONDS
TARGET_WINDOW_SAMPLES = TARGET_RATE_HZ * WINDOW_SECONDS
GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True, slots=True)
class ParticipantWindows:
    participant_id: str
    windows: np.ndarray
    labels: np.ndarray
    references: tuple["WindowReference", ...]
    label_counts: dict[str, int]
    raw_annotation_counts: dict[str, int]
    source_rows_scanned: int
    scan_stopped_after_selection_complete: bool


@dataclass(frozen=True, slots=True)
class WindowReference:
    participant_id: str
    mapped_label: str
    source_member: str
    source_start_row: int
    source_end_row: int


@dataclass(frozen=True, slots=True)
class SoftmaxModel:
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    weights: np.ndarray
    bias: np.ndarray
    final_loss: float


def map_annotation(annotation: str) -> str | None:
    normalized = re.sub(r"\s+", " ", annotation.strip().lower())
    if not normalized or normalized in {"nan", "none", "unknown"}:
        return None
    if any(word in normalized for word in ("sleep", "asleep", "lying", "lie down", "in bed")):
        return "sleep_or_lying_candidate"
    if (
        ";eating;" in normalized
        or ";drinking;" in normalized
        or re.search(r"(?:^|;)\d+\s+(?:eating|drinking)\b", normalized)
    ):
        return "eating_candidate"
    if ";walking;" in normalized or "walking " in normalized or "stroll" in normalized:
        return "walking"
    return "other_unknown"


def downsample_window(source_window_g: np.ndarray) -> np.ndarray:
    values = np.asarray(source_window_g, dtype=np.float32)
    if values.shape != (SOURCE_WINDOW_SAMPLES, 3):
        raise ValueError(f"原始活动窗口必须是 ({SOURCE_WINDOW_SAMPLES}, 3)。")
    if not np.isfinite(values).all():
        raise ValueError("原始活动窗口不能包含 NaN 或无穷值。")
    factor = SOURCE_RATE_HZ // TARGET_RATE_HZ
    if SOURCE_RATE_HZ % TARGET_RATE_HZ:
        raise RuntimeError("首版活动重采样只支持整数降采样因子。")
    # Five-sample boxcar mean is an explicit low-pass stage before decimation.
    reduced_g = values.reshape(TARGET_WINDOW_SAMPLES, factor, 3).mean(axis=1)
    return (reduced_g * GRAVITY_M_S2).astype(np.float32)


def extract_features(windows: np.ndarray) -> np.ndarray:
    values = np.asarray(windows, dtype=np.float32)
    if values.ndim != 3 or values.shape[1:] != (TARGET_WINDOW_SAMPLES, 3):
        raise ValueError("活动特征输入必须是 [batch, 400, 3]。")
    mean = values.mean(axis=1)
    std = values.std(axis=1)
    mean_abs = np.abs(values).mean(axis=1)
    magnitude = np.sqrt(np.sum(values * values, axis=2))
    magnitude_mean = magnitude.mean(axis=1, keepdims=True)
    magnitude_std = magnitude.std(axis=1, keepdims=True)
    return np.concatenate(
        (mean, std, mean_abs, magnitude_mean, magnitude_std),
        axis=1,
    ).astype(np.float32)


def _open_nested_gzip(archive: zipfile.ZipFile, member: str) -> BinaryIO:
    return gzip.GzipFile(fileobj=archive.open(member, "r"), mode="rb")


def load_participant_windows(
    archive_path: Path,
    participant_id: str,
    *,
    per_class_limit: int,
) -> ParticipantWindows:
    member = f"capture24/{participant_id}.csv.gz"
    windows: list[np.ndarray] = []
    labels: list[int] = []
    references: list[WindowReference] = []
    label_counts: Counter[str] = Counter()
    raw_counts: Counter[str] = Counter()
    current_label: str | None = None
    current_samples: list[tuple[float, float, float]] = []
    current_source_rows: list[int] = []
    source_rows_scanned = 0
    scan_stopped_after_selection_complete = False

    def selection_complete() -> bool:
        return all(label_counts[label] >= per_class_limit for label in LABELS)

    def flush_complete_windows() -> None:
        nonlocal current_samples, current_source_rows
        if current_label is None:
            current_samples = []
            current_source_rows = []
            return
        while (
            len(current_samples) >= SOURCE_WINDOW_SAMPLES
            and label_counts[current_label] < per_class_limit
        ):
            source_window = np.asarray(
                current_samples[:SOURCE_WINDOW_SAMPLES], dtype=np.float32
            )
            source_rows = current_source_rows[:SOURCE_WINDOW_SAMPLES]
            del current_samples[:SOURCE_WINDOW_SAMPLES]
            del current_source_rows[:SOURCE_WINDOW_SAMPLES]
            windows.append(downsample_window(source_window))
            labels.append(LABEL_TO_INDEX[current_label])
            references.append(
                WindowReference(
                    participant_id=participant_id,
                    mapped_label=current_label,
                    source_member=member,
                    source_start_row=source_rows[0],
                    source_end_row=source_rows[-1],
                )
            )
            label_counts[current_label] += 1
        if label_counts[current_label] >= per_class_limit:
            current_samples = []
            current_source_rows = []

    with zipfile.ZipFile(archive_path) as archive:
        if member not in archive.namelist():
            raise FileNotFoundError(f"CAPTURE-24 压缩包缺少 {member}。")
        with _open_nested_gzip(archive, member) as compressed:
            text = io.TextIOWrapper(compressed, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text)
            required = {"x", "y", "z", "annotation"}
            if reader.fieldnames is None or not required <= set(reader.fieldnames):
                raise ValueError(f"{member} 缺少列：{sorted(required)}")
            for row_index, row in enumerate(reader, start=2):
                source_rows_scanned += 1
                annotation = row["annotation"] or ""
                target = map_annotation(annotation)
                if annotation:
                    raw_counts[annotation] += 1
                if target != current_label:
                    flush_complete_windows()
                    if selection_complete():
                        scan_stopped_after_selection_complete = True
                        break
                    current_samples = []
                    current_source_rows = []
                    current_label = target
                if target is None or label_counts[target] >= per_class_limit:
                    continue
                try:
                    sample = (float(row["x"]), float(row["y"]), float(row["z"]))
                except (TypeError, ValueError):
                    current_samples = []
                    current_source_rows = []
                    current_label = None
                    continue
                if not all(np.isfinite(value) for value in sample):
                    current_samples = []
                    current_source_rows = []
                    current_label = None
                    continue
                current_samples.append(sample)
                current_source_rows.append(row_index)
                if len(current_samples) >= SOURCE_WINDOW_SAMPLES:
                    flush_complete_windows()
                    if selection_complete():
                        scan_stopped_after_selection_complete = True
                        break
            if not scan_stopped_after_selection_complete:
                flush_complete_windows()
    if not windows:
        array = np.empty((0, TARGET_WINDOW_SAMPLES, 3), dtype=np.float32)
    else:
        array = np.stack(windows).astype(np.float32)
    return ParticipantWindows(
        participant_id=participant_id,
        windows=array,
        labels=np.asarray(labels, dtype=np.int64),
        references=tuple(references),
        label_counts=dict(sorted(label_counts.items())),
        raw_annotation_counts=dict(sorted(raw_counts.items())),
        source_rows_scanned=source_rows_scanned,
        scan_stopped_after_selection_complete=scan_stopped_after_selection_complete,
    )


def combine_participants(
    participants: Sequence[ParticipantWindows],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    nonempty = [participant for participant in participants if len(participant.windows)]
    if not nonempty:
        raise ValueError("没有可组合的活动窗口。")
    return (
        np.concatenate([participant.windows for participant in nonempty]),
        np.concatenate([participant.labels for participant in nonempty]),
        np.concatenate(
            [
                np.repeat(participant.participant_id, len(participant.labels))
                for participant in nonempty
            ]
        ),
    )


def train_softmax(
    windows: np.ndarray,
    labels: np.ndarray,
    *,
    iterations: int = 1200,
    learning_rate: float = 0.05,
    l2: float = 0.001,
) -> SoftmaxModel:
    features = extract_features(windows).astype(np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    if set(labels.tolist()) != set(range(len(LABELS))):
        raise ValueError("活动训练集必须包含四个目标类别。")
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-6] = 1.0
    normalized = (features - mean) / scale
    weights = np.zeros((normalized.shape[1], len(LABELS)), dtype=np.float64)
    bias = np.zeros(len(LABELS), dtype=np.float64)
    class_counts = np.bincount(labels, minlength=len(LABELS)).astype(np.float64)
    sample_weights = len(labels) / (len(LABELS) * class_counts[labels])
    targets = np.eye(len(LABELS), dtype=np.float64)[labels]
    final_loss = 0.0
    for _ in range(iterations):
        logits = normalized @ weights + bias
        logits -= logits.max(axis=1, keepdims=True)
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        error = (probabilities - targets) * sample_weights[:, None]
        weights -= learning_rate * (
            normalized.T @ error / len(labels) + l2 * weights
        )
        bias -= learning_rate * error.mean(axis=0)
    # Recompute after the final optimizer update so the reported value describes
    # the persisted coefficients rather than the penultimate step.
    final_logits = normalized @ weights + bias
    final_logits -= final_logits.max(axis=1, keepdims=True)
    final_probabilities = np.exp(final_logits)
    final_probabilities /= final_probabilities.sum(axis=1, keepdims=True)
    final_loss = float(
        -np.mean(
            sample_weights
            * np.log(
                np.clip(
                    final_probabilities[np.arange(len(labels)), labels],
                    1e-9,
                    1,
                )
            )
        )
        + 0.5 * l2 * np.sum(weights * weights)
    )
    return SoftmaxModel(
        feature_mean=mean.astype(np.float32),
        feature_scale=scale.astype(np.float32),
        weights=weights.astype(np.float32),
        bias=bias.astype(np.float32),
        final_loss=final_loss,
    )


def predict_softmax(model: SoftmaxModel, windows: np.ndarray) -> np.ndarray:
    features = extract_features(windows)
    normalized = (features - model.feature_mean) / model.feature_scale
    logits = normalized @ model.weights + model.bias
    logits -= logits.max(axis=1, keepdims=True)
    probabilities = np.exp(logits)
    return (probabilities / probabilities.sum(axis=1, keepdims=True)).astype(np.float32)


def classification_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, object]:
    labels = np.asarray(labels, dtype=np.int64)
    predictions = np.asarray(probabilities).argmax(axis=1)
    matrix = np.zeros((len(LABELS), len(LABELS)), dtype=np.int64)
    for truth, prediction in zip(labels, predictions, strict=True):
        matrix[truth, prediction] += 1
    per_class: dict[str, dict[str, float | int | None]] = {}
    f1_values: list[float] = []
    for index, label in enumerate(LABELS):
        tp = int(matrix[index, index])
        fp = int(matrix[:, index].sum() - tp)
        fn = int(matrix[index, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision is not None and recall is not None and precision + recall
            else None
        )
        if f1 is not None:
            f1_values.append(f1)
        per_class[label] = {
            "support": int(matrix[index, :].sum()),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return {
        "labels": list(LABELS),
        "confusion_matrix": matrix.tolist(),
        "accuracy": float(np.mean(predictions == labels)),
        "macro_f1": float(np.mean(f1_values)) if f1_values else None,
        "per_class": per_class,
    }


def build_onnx(model: SoftmaxModel, output_path: Path) -> None:
    input_info = helper.make_tensor_value_info(
        "acceleration_window",
        TensorProto.FLOAT,
        ["batch", TARGET_WINDOW_SAMPLES, 3],
    )
    output_info = helper.make_tensor_value_info(
        "activity_probabilities",
        TensorProto.FLOAT,
        ["batch", len(LABELS)],
    )
    initializers = [
        numpy_helper.from_array(model.feature_mean, name="feature_mean"),
        numpy_helper.from_array(model.feature_scale, name="feature_scale"),
        numpy_helper.from_array(model.weights, name="classifier_weights"),
        numpy_helper.from_array(model.bias, name="classifier_bias"),
    ]
    nodes = [
        helper.make_node("ReduceMean", ["acceleration_window"], ["axis_mean"], axes=[1], keepdims=0),
        helper.make_node("ReduceMean", ["acceleration_window"], ["axis_mean_keep"], axes=[1], keepdims=1),
        helper.make_node("Sub", ["acceleration_window", "axis_mean_keep"], ["axis_centered"]),
        helper.make_node("Mul", ["axis_centered", "axis_centered"], ["axis_squared"]),
        helper.make_node("ReduceMean", ["axis_squared"], ["axis_variance"], axes=[1], keepdims=0),
        helper.make_node("Sqrt", ["axis_variance"], ["axis_std"]),
        helper.make_node("Abs", ["acceleration_window"], ["axis_abs"]),
        helper.make_node("ReduceMean", ["axis_abs"], ["axis_mean_abs"], axes=[1], keepdims=0),
        helper.make_node("Mul", ["acceleration_window", "acceleration_window"], ["sample_squared"]),
        helper.make_node("ReduceSum", ["sample_squared"], ["magnitude_squared"], axes=[2], keepdims=0),
        helper.make_node("Sqrt", ["magnitude_squared"], ["magnitude"]),
        helper.make_node("ReduceMean", ["magnitude"], ["magnitude_mean"], axes=[1], keepdims=1),
        helper.make_node("Sub", ["magnitude", "magnitude_mean"], ["magnitude_centered"]),
        helper.make_node("Mul", ["magnitude_centered", "magnitude_centered"], ["magnitude_squared_centered"]),
        helper.make_node("ReduceMean", ["magnitude_squared_centered"], ["magnitude_variance"], axes=[1], keepdims=1),
        helper.make_node("Sqrt", ["magnitude_variance"], ["magnitude_std"]),
        helper.make_node(
            "Concat",
            ["axis_mean", "axis_std", "axis_mean_abs", "magnitude_mean", "magnitude_std"],
            ["features"],
            axis=1,
        ),
        helper.make_node("Sub", ["features", "feature_mean"], ["features_centered"]),
        helper.make_node("Div", ["features_centered", "feature_scale"], ["features_normalized"]),
        helper.make_node(
            "Gemm",
            ["features_normalized", "classifier_weights", "classifier_bias"],
            ["logits"],
        ),
        helper.make_node("Softmax", ["logits"], ["activity_probabilities"], axis=1),
    ]
    graph = helper.make_graph(
        nodes,
        "capture24_activity_linear_features",
        [input_info],
        [output_info],
        initializer=initializers,
    )
    model_proto = helper.make_model(
        graph,
        producer_name="smartwatch-health-simulator",
        opset_imports=[helper.make_opsetid("", 12)],
    )
    model_proto.metadata_props.add(key="labels", value=",".join(LABELS))
    model_proto.metadata_props.add(
        key="input_units", value="m/s^2"
    )
    onnx.checker.check_model(model_proto)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model_proto, output_path)
