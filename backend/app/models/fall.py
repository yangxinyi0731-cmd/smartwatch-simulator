from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort

from ..contracts import ModelKind, ModelManifest


class FallModelAdapter:
    """Strict CPU adapter for the research-only 200x6 fall candidate model."""

    def __init__(self, *, project_root: Path, manifest_path: Path) -> None:
        self.project_root = project_root.resolve()
        self.manifest_path = manifest_path.resolve()
        self.manifest = ModelManifest.model_validate_json(
            self.manifest_path.read_text(encoding="utf-8")
        )
        if self.manifest.model_kind is not ModelKind.FALL_DETECTION:
            raise ValueError("跌倒适配器只能加载 FALL_DETECTION manifest。")
        if self.manifest.deployment_approved:
            raise ValueError("当前适配器只允许加载未获部署批准的研究模型。")
        if self.manifest.artifact_relative_path is None:
            raise ValueError("跌倒模型 manifest 缺少 ONNX 文件路径。")
        artifact_path = (self.project_root / self.manifest.artifact_relative_path).resolve()
        if self.project_root not in artifact_path.parents:
            raise ValueError("跌倒模型文件必须位于项目目录内。")
        if not artifact_path.is_file():
            raise FileNotFoundError(f"跌倒模型文件不存在：{artifact_path}")
        artifact_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if artifact_hash != self.manifest.artifact_sha256:
            raise ValueError("跌倒模型 ONNX 文件哈希与 manifest 不一致。")

        self.session = ort.InferenceSession(
            str(artifact_path),
            providers=["CPUExecutionProvider"],
        )
        inputs = self.session.get_inputs()
        outputs = self.session.get_outputs()
        if len(inputs) != 1 or inputs[0].name != "imu_window":
            raise ValueError("跌倒模型必须只有名为 imu_window 的输入。")
        if tuple(inputs[0].shape) != ("batch", 200, 6):
            raise ValueError(f"跌倒模型输入形状不符合 200×6 合同：{inputs[0].shape}")
        if inputs[0].type != "tensor(float)":
            raise ValueError("跌倒模型输入必须是 float32。")
        if len(outputs) != 1 or outputs[0].name != "fall_probability":
            raise ValueError("跌倒模型必须只有名为 fall_probability 的输出。")
        self.input_name = inputs[0].name
        self.output_name = outputs[0].name

    def predict_fall_probability(self, windows: np.ndarray) -> np.ndarray:
        values = np.asarray(windows, dtype=np.float32)
        if values.ndim != 3 or values.shape[1:] != (200, 6):
            raise ValueError("跌倒模型输入必须是 [batch, 200, 6]。")
        if len(values) == 0:
            raise ValueError("跌倒模型输入批次不能为空。")
        if not np.isfinite(values).all():
            raise ValueError("跌倒模型输入不能包含 NaN 或无穷值。")
        output = np.asarray(
            self.session.run([self.output_name], {self.input_name: values})[0],
            dtype=np.float32,
        ).reshape(-1)
        if output.shape != (len(values),):
            raise ValueError("跌倒模型输出批次大小与输入不一致。")
        if not np.isfinite(output).all() or np.any((output < 0) | (output > 1)):
            raise ValueError("跌倒模型输出必须是 0 到 1 的有限概率。")
        return output

    @property
    def threshold(self) -> float:
        source_manifest_path = self.manifest_path.with_name("source_manifest.json")
        payload = json.loads(source_manifest_path.read_text(encoding="utf-8"))
        value = float(payload["output"]["threshold"])
        if not 0 <= value <= 1:
            raise ValueError("来源 manifest 的阈值必须位于 0 到 1。")
        return value
