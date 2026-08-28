from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import onnxruntime as ort

from ..contracts import ModelKind, ModelManifest
from ..training.activity import LABELS, TARGET_WINDOW_SAMPLES


class ActivityModelAdapter:
    def __init__(self, *, project_root: Path, manifest_path: Path) -> None:
        self.project_root = project_root.resolve()
        self.manifest_path = manifest_path.resolve()
        self.manifest = ModelManifest.model_validate_json(
            self.manifest_path.read_text(encoding="utf-8")
        )
        if self.manifest.model_kind is not ModelKind.ACTIVITY_RECOGNITION:
            raise ValueError("活动适配器只能加载 ACTIVITY_RECOGNITION manifest。")
        if self.manifest.deployment_approved:
            raise ValueError("当前活动适配器只允许研究模型。")
        if self.manifest.artifact_relative_path is None:
            raise ValueError("活动模型 manifest 缺少 ONNX 文件。")
        artifact = (self.project_root / self.manifest.artifact_relative_path).resolve()
        if self.project_root not in artifact.parents:
            raise ValueError("活动模型文件必须位于项目目录内。")
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != self.manifest.artifact_sha256:
            raise ValueError("活动模型文件哈希与 manifest 不一致。")
        self.session = ort.InferenceSession(str(artifact), providers=["CPUExecutionProvider"])
        inputs = self.session.get_inputs()
        outputs = self.session.get_outputs()
        if len(inputs) != 1 or inputs[0].name != "acceleration_window":
            raise ValueError("活动模型必须只有 acceleration_window 输入。")
        if tuple(inputs[0].shape) != ("batch", TARGET_WINDOW_SAMPLES, 3):
            raise ValueError("活动模型输入形状必须是 [batch, 400, 3]。")
        if len(outputs) != 1 or outputs[0].name != "activity_probabilities":
            raise ValueError("活动模型必须只有 activity_probabilities 输出。")
        self.input_name = inputs[0].name
        self.output_name = outputs[0].name

    def predict_probabilities(self, windows: np.ndarray) -> np.ndarray:
        values = np.asarray(windows, dtype=np.float32)
        if values.ndim != 3 or values.shape[1:] != (TARGET_WINDOW_SAMPLES, 3):
            raise ValueError("活动模型输入必须是 [batch, 400, 3]。")
        if len(values) == 0 or not np.isfinite(values).all():
            raise ValueError("活动模型输入必须是非空有限数值批次。")
        probabilities = np.asarray(
            self.session.run([self.output_name], {self.input_name: values})[0],
            dtype=np.float32,
        )
        if probabilities.shape != (len(values), len(LABELS)):
            raise ValueError("活动模型输出形状与四分类合同不一致。")
        if not np.isfinite(probabilities).all():
            raise ValueError("活动模型输出包含非有限数值。")
        if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-4):
            raise ValueError("活动模型四类概率之和必须为 1。")
        return probabilities
