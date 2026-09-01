from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sqlite3
from dataclasses import asdict
from datetime import datetime
from functools import lru_cache
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from math import ceil
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import numpy as np
import yaml

from backend.app.config import Settings
from backend.app.database import Database
from research.early_risk.common import PROJECT_ROOT, sha256_file
from research.early_risk.policy import PolicyConfig, PolicyInput, run_dry_policy
from research.early_risk.upload_analysis import (
    MAX_UPLOAD_BYTES,
    analyze_normalized_imu,
    analyze_upload_request,
)


WORKBENCH_ROOT = Path(__file__).with_name("workbench")
TARGET_CONTRACT_PATH = PROJECT_ROOT / "configs" / "early_risk" / "target_contract.v1.yaml"
BASELINE_CONFIG_PATH = PROJECT_ROOT / "configs" / "early_risk" / "baselines.v1.yaml"
FIXTURE_PATH = (
    PROJECT_ROOT
    / "tests"
    / "early_risk"
    / "fixtures"
    / "deterministic_timeline.v1.json"
)
GATE_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "early_risk" / "e0" / "p0_p2_gate_summary.json"
)
FIXTURE_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "early_risk" / "e0" / "fixture_benchmark.json"
)
DATA_AUDIT_PATH = (
    PROJECT_ROOT / "reports" / "early_risk" / "e0" / "current_data_audit.json"
)
ROUTINE_CASE_PATH = PROJECT_ROOT / "data" / "cases" / "synthetic_routine_100_v1.json"
PUBLIC_RISK_MANIFEST_PATH = (
    PROJECT_ROOT / "models" / "early_risk" / "public_weda_linear_v1" / "manifest.json"
)
PUBLIC_RISK_REPORT_PATH = (
    PROJECT_ROOT / "reports" / "early_risk" / "public_weda_linear_v1.json"
)
SELF_COLLECTED_REGISTRY_PATH = (
    PROJECT_ROOT / "data" / "catalog" / "self_collected_pending_v1.json"
)
NEW_DATA_FORMAT_PATH = PROJECT_ROOT / "docs" / "early_risk" / "NEW_DATA_FORMAT.md"

MAX_SIMULATE_REQUEST_BYTES = 16 * 1024
MAX_UPLOAD_REQUEST_BYTES = int(MAX_UPLOAD_BYTES * 4 / 3) + 64 * 1024
MAX_EVIDENCE_POINTS = 240
ROUTINE_DISPLAY_DAYS = 14
DOWNLOADS: dict[str, Path] = {
    "target-contract.yaml": TARGET_CONTRACT_PATH,
    "gate-summary.json": GATE_REPORT_PATH,
    "fixture-benchmark.json": FIXTURE_REPORT_PATH,
    "current-data-audit.json": DATA_AUDIT_PATH,
    "deterministic-timeline.json": FIXTURE_PATH,
    "public-risk-manifest.json": PUBLIC_RISK_MANIFEST_PATH,
    "public-risk-evaluation.json": PUBLIC_RISK_REPORT_PATH,
    "new-data-format.md": NEW_DATA_FORMAT_PATH,
}

PIPELINE_STAGES: tuple[dict[str, str], ...] = (
    {
        "stage": "P0",
        "title": "目标与证据合同",
        "state": "engineering_pass",
        "detail": "工程冻结完成；正式三方签署待完成。",
    },
    {
        "stage": "P1",
        "title": "数据与标签合同",
        "state": "engineering_pass",
        "detail": "Schema、传感器配置和负例拒绝测试已通过。",
    },
    {
        "stage": "P2",
        "title": "离线评估骨架",
        "state": "engineering_pass",
        "detail": "防泄漏、指标和 dry-run 状态机可重复运行。",
    },
    {
        "stage": "P3",
        "title": "伦理、许可与采集",
        "state": "locked",
        "detail": "等待正式签署、伦理、许可和用户单独授权。",
    },
    {
        "stage": "P4",
        "title": "真实个体基线",
        "state": "locked",
        "detail": "没有 28 个有效日的获批真实个人数据。",
    },
    {
        "stage": "P5",
        "title": "预事件模型",
        "state": "locked",
        "detail": "没有满足事件数、人群和无事件人日 Gate 的数据。",
    },
    {
        "stage": "P6",
        "title": "融合与策略仿真",
        "state": "locked",
        "detail": "当前仅有确定性工程夹具状态机。",
    },
    {
        "stage": "P7",
        "title": "内外部验证",
        "state": "locked",
        "detail": "没有冻结系统的独立外部验证。",
    },
    {
        "stage": "P8",
        "title": "前瞻静默试运行",
        "state": "locked",
        "detail": "没有获批静默期、目标人日或前瞻事件。",
    },
    {
        "stage": "P9",
        "title": "受控风险界面与通知",
        "state": "locked",
        "detail": "产品风险界面和真实通知保持关闭。",
    },
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} 顶层必须是对象。")
    return payload


def _read_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} 顶层必须是对象。")
    return payload


def _downsample_indices(sample_count: int) -> tuple[int, ...]:
    if sample_count < 2:
        raise ValueError("传感器记录至少需要两个采样点。")
    stride = max(1, ceil(sample_count / MAX_EVIDENCE_POINTS))
    indices = list(range(0, sample_count, stride))
    if indices[-1] != sample_count - 1:
        indices.append(sample_count - 1)
    return tuple(indices)


def _build_sensor_evidence(case_id: str) -> dict[str, Any]:
    settings = Settings.from_environment()
    if not settings.database_path.is_file():
        raise FileNotFoundError("本机案例数据库不存在。")

    bundle = Database(settings.database_path).get_case_runtime_bundle(case_id)
    if bundle is None:
        raise LookupError("没有找到这组已登记案例。")
    if len(bundle.streams) != 1:
        raise ValueError("该案例必须且只能有一条已登记传感器流。")

    stream = bundle.streams[0]
    path = (PROJECT_ROOT / stream.relative_path).resolve()
    if PROJECT_ROOT not in path.parents or not path.is_file():
        raise FileNotFoundError("案例登记的本地传感器文件不存在。")
    if hashlib.sha256(path.read_bytes()).hexdigest() != stream.content_sha256:
        raise ValueError("案例传感器文件哈希与登记记录不一致。")
    if stream.storage_format.value != "NPY":
        raise ValueError("判断依据只读取已核验的 NPY 传感器流。")

    values = np.load(path, allow_pickle=False)
    if values.shape != (stream.sample_count, len(stream.channels)):
        raise ValueError("传感器数组形状与登记记录不一致。")
    if values.dtype != np.float32 or not np.isfinite(values).all():
        raise ValueError("传感器数组必须是有限 float32 数值。")

    channel_index = {name: index for index, name in enumerate(stream.channels)}
    acceleration_indices = [channel_index[name] for name in ("ax", "ay", "az")]
    acceleration = np.linalg.norm(values[:, acceleration_indices], axis=1)
    series: list[dict[str, Any]] = [
        {
            "id": "acceleration_magnitude",
            "label": "加速度合量",
            "unit": "m/s²",
            "values": [],
        }
    ]
    angular_velocity: np.ndarray | None = None
    if all(name in channel_index for name in ("gx", "gy", "gz")):
        gyroscope_indices = [channel_index[name] for name in ("gx", "gy", "gz")]
        angular_velocity = np.linalg.norm(values[:, gyroscope_indices], axis=1)
        series.append(
            {
                "id": "angular_velocity_magnitude",
                "label": "角速度合量",
                "unit": "rad/s",
                "values": [],
            }
        )

    indices = _downsample_indices(stream.sample_count)
    for index in indices:
        offset_ms = int(round(index * 1000 / stream.sample_rate_hz))
        series[0]["values"].append([offset_ms, round(float(acceleration[index]), 6)])
        if angular_velocity is not None:
            series[1]["values"].append(
                [offset_ms, round(float(angular_velocity[index]), 6)]
            )

    quality = bundle.qualities[0] if bundle.qualities else None
    analysis: dict[str, Any] | None = None
    if values.shape[1] == 6 and float(stream.sample_rate_hz) == 50.0:
        analysis = analyze_normalized_imu(values)
        fall_events = [
            event for event in bundle.ground_truth_events if event.event_type.value == "FALL_INTERVAL"
        ]
        analysis["early_risk_model"]["proxy_anchor_offset_ms"] = (
            fall_events[0].start_offset_ms if len(fall_events) == 1 else None
        )

    return {
        "case_id": case_id,
        "evidence_type": "sensor_waveform",
        "source_label": bundle.case.source.dataset_name,
        "truth_category": bundle.case.truth_category.value,
        "content_verified": True,
        "stream": {
            "sample_rate_hz": stream.sample_rate_hz,
            "sample_count": stream.sample_count,
            "displayed_point_count": len(indices),
            "duration_ms": stream.duration_ms,
            "channels": list(stream.channels),
            "axis_count": len(stream.channels),
        },
        "quality": {
            "flag_count": len(quality.flags) if quality is not None else 0,
            "flags": list(quality.flags) if quality is not None else [],
        },
        "events": [
            {
                "event_type": event.event_type.value,
                "label": event.label,
                "start_offset_ms": event.start_offset_ms,
                "end_offset_ms": event.end_offset_ms,
            }
            for event in bundle.ground_truth_events
        ],
        "series": series,
        "analysis": analysis,
        "limitations": [
            "波形来自本机已登记文件，经内容哈希和数组形状核对后抽样显示。",
            "合量曲线由三个真实方向轴计算，用于简化读图，不表示某个方向或身体部位造成了结果。",
            "六轴 WEDA 案例会在请求时真实运行三个研究模型；1/2/3 秒输出只对应公开受控数据代理标签，不构成现实报警。",
        ],
    }


def _build_routine_evidence(case_id: str) -> dict[str, Any]:
    if case_id != "synthetic-routine-100-v1":
        raise LookupError("没有找到这组合成规律案例。")
    payload = _read_json(ROUTINE_CASE_PATH)
    events = payload.get("events")
    if not isinstance(events, list) or not events:
        raise ValueError("合成规律案例没有可显示的事件。")

    grouped: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        started_at = datetime.fromisoformat(str(event["started_at"]))
        day = started_at.date().isoformat()
        grouped.setdefault(day, []).append(
            {
                "event_type": str(event["event_type"]),
                "slot_key": str(event["slot_key"]),
                "start_minute": round(
                    started_at.hour * 60
                    + started_at.minute
                    + started_at.second / 60,
                    2,
                ),
                "duration_minutes": round(float(event["duration_minutes"]), 2),
            }
        )
    displayed_days = sorted(grouped)[-ROUTINE_DISPLAY_DAYS:]
    return {
        "case_id": case_id,
        "evidence_type": "synthetic_routine_timeline",
        "source_label": "固定种子合成生活规律",
        "truth_category": "SYNTHETIC_ROUTINE",
        "content_verified": True,
        "profile": {
            "history_days": int(payload["history_days"]),
            "event_count": len(events),
            "seed": int(payload["seed"]),
            "displayed_day_count": len(displayed_days),
        },
        "days": [
            {"day": day, "events": grouped[day]}
            for day in displayed_days
        ],
        "limitations": [
            "时间图来自固定种子生成的合成生活事件，不是参与者生活记录。",
            "生活规律案例没有腕部传感器流，因此不伪造波形，改用最近 14 天事件时间图。",
            "此依据只演示规律比较的输入结构，不构成医学风险判断。",
        ],
    }


@lru_cache(maxsize=128)
def build_case_evidence(case_id: str) -> dict[str, Any]:
    if not case_id or len(case_id) > 128 or "/" in case_id or "\\" in case_id:
        raise LookupError("案例编号无效。")
    if case_id == "synthetic-routine-100-v1":
        return _build_routine_evidence(case_id)
    return _build_sensor_evidence(case_id)


def build_workbench_payload() -> dict[str, Any]:
    contract = _read_yaml(TARGET_CONTRACT_PATH)
    baseline_config = _read_yaml(BASELINE_CONFIG_PATH)
    gate = _read_json(GATE_REPORT_PATH)
    fixture_report = _read_json(FIXTURE_REPORT_PATH)
    audit = _read_json(DATA_AUDIT_PATH)
    fixture = _read_json(FIXTURE_PATH)
    public_risk_manifest = _read_json(PUBLIC_RISK_MANIFEST_PATH)
    public_risk_report = _read_json(PUBLIC_RISK_REPORT_PATH)
    self_collected = _read_json(SELF_COLLECTED_REGISTRY_PATH)

    gate_results = gate["results"]
    audit_results = audit["results"]
    fixture_results = fixture_report["results"]
    policy_config = baseline_config["policy_fixture"]

    return {
        "meta": {
            "product_name": "模拟手表风险评估工作台",
            "page_title": "公开数据真模型运行与新数据检测",
            "evidence_level": gate["evidence_level"],
            "prediction_evidence": gate["prediction_evidence"],
            "public_proxy_model_ready": True,
            "real_world_prediction_evidence": False,
            "self_collected_validation_complete": False,
            "deployment_approved": gate["deployment_approved"],
            "engineering_status": gate_results["overall"]["engineering_status"],
            "formal_signoff_complete": gate_results["overall"]["formal_signoff_complete"],
            "next_stage_authorized": gate_results["overall"]["next_stage_authorized"],
        },
        "truth": {
            "product_definition": contract["product_definition"],
            "allowed_claims": contract["allowed_e0_claims"],
            "limitations": gate["limitations"],
            "notice": (
                "本工作台会对六轴公开案例和用户选择的新文件真实运行研究模型，"
                "并逐秒显示 1、2、3 秒代理风险、波形依据和格式化结论。上传文件"
                "只在内存中分析，不写入案例库，也不会发送任何通知。"
            ),
        },
        "public_risk_model": {
            "manifest_id": public_risk_manifest["manifest_id"],
            "model_id": public_risk_manifest["model_id"],
            "status": "PUBLIC_PROXY_BASELINE_READY",
            "proxy_anchor": public_risk_manifest["proxy_anchor"],
            "participant_disjoint": public_risk_manifest["participant_disjoint"],
            "evaluation_snapshot_at_exact_lead": public_risk_report[
                "evaluation_snapshot_at_exact_lead"
            ],
            "limitations": public_risk_report["limitations"],
            "manifest_sha256": sha256_file(PUBLIC_RISK_MANIFEST_PATH),
            "report_sha256": sha256_file(PUBLIC_RISK_REPORT_PATH),
        },
        "self_collected": {
            "status": self_collected["status"],
            "expected_case_count": self_collected["expected_case_count"],
            "received_case_count": self_collected["received_case_count"],
            "accepted_case_count": self_collected["accepted_case_count"],
            "cases": self_collected["cases"],
            "claim_enabled": False,
            "note": self_collected["note"],
        },
        "pipeline": list(PIPELINE_STAGES),
        "contract": {
            "id": contract["contract_id"],
            "version": contract["version"],
            "status": contract["status"],
            "frozen_date": contract["frozen_date"],
            "events": contract["target_events"],
            "time_anchors": contract["time_anchors"],
            "immediate_horizons_seconds": contract["immediate_horizons_seconds"],
            "background_horizons_hours": contract["background_horizons_hours"],
            "required_metric_ids": contract["required_metric_ids"],
            "synchronization_error_limit_ms": contract["synchronization_error_limit_ms"],
            "external_approval_state": contract["external_approval_state"],
            "sha256": gate_results["p0"]["contract_canonical_sha256"],
        },
        "gate": {
            "p0": gate_results["p0"],
            "p1": gate_results["p1"],
            "p2": gate_results["p2"],
            "required_external_actions": gate_results[
                "required_external_actions_before_p3"
            ],
        },
        "audit": {
            "audited_asset_count": audit_results["audited_asset_count"],
            "expected_asset_count": audit_results["expected_asset_count"],
            "asset_coverage": audit_results["asset_coverage"],
            "no_download_performed": audit_results["no_download_performed"],
            "usage_matrix": audit_results["usage_matrix"],
            "model_registry": audit_results["model_registry"],
            "limitations": audit["limitations"],
        },
        "fixture": {
            "id": fixture["fixture_id"],
            "version": fixture["version"],
            "timeline_samples": fixture["timeline_samples"],
            "events": fixture["events"],
            "alerts": fixture["alerts"],
            "policy_inputs": fixture["policy_inputs"],
            "default_policy": policy_config,
            "metrics": fixture_results["metrics"],
            "suppression_impact": fixture_results["suppression_impact"],
            "temporal_leakage": fixture_results["temporal_leakage"],
            "limitations": fixture_report["limitations"],
            "canonical_sha256": gate_results["p2"]["fixture_canonical_sha256"],
        },
        "downloads": [
            {
                "name": name,
                "href": f"/evidence/{name}",
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for name, path in DOWNLOADS.items()
        ],
    }


def simulate_policy(payload: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = {
        "threshold_on",
        "threshold_off",
        "consecutive_required",
        "cooldown_ms",
    }
    extra_fields = sorted(set(payload) - allowed_fields)
    if extra_fields:
        raise ValueError(f"不支持的参数：{', '.join(extra_fields)}")

    baseline_config = _read_yaml(BASELINE_CONFIG_PATH)["policy_fixture"]
    fixture = _read_json(FIXTURE_PATH)
    resolved = {
        "threshold_on": payload.get("threshold_on", baseline_config["threshold_on"]),
        "threshold_off": payload.get("threshold_off", baseline_config["threshold_off"]),
        "consecutive_required": payload.get(
            "consecutive_required", baseline_config["consecutive_required"]
        ),
        "cooldown_ms": payload.get("cooldown_ms", baseline_config["cooldown_ms"]),
        "dry_run": True,
    }

    threshold_on_value = resolved["threshold_on"]
    threshold_off_value = resolved["threshold_off"]
    consecutive_value = resolved["consecutive_required"]
    cooldown_value = resolved["cooldown_ms"]
    if (
        isinstance(threshold_on_value, bool)
        or not isinstance(threshold_on_value, (int, float))
        or isinstance(threshold_off_value, bool)
        or not isinstance(threshold_off_value, (int, float))
    ):
        raise ValueError("触发阈值和复位阈值必须是 JSON 数字。")
    if isinstance(consecutive_value, bool) or not isinstance(consecutive_value, int):
        raise ValueError("连续证据数必须是 JSON 整数。")
    if isinstance(cooldown_value, bool) or not isinstance(cooldown_value, int):
        raise ValueError("冷却时间必须是 JSON 整数。")

    threshold_on = float(threshold_on_value)
    threshold_off = float(threshold_off_value)
    consecutive_required = consecutive_value
    cooldown_ms = cooldown_value

    if not 0.51 <= threshold_on <= 0.99:
        raise ValueError("触发阈值必须在 0.51–0.99。")
    if not 0 <= threshold_off <= 0.90:
        raise ValueError("复位阈值必须在 0–0.90。")
    if not 1 <= consecutive_required <= 5:
        raise ValueError("连续证据数必须在 1–5。")
    if not 0 <= cooldown_ms <= 30_000:
        raise ValueError("冷却时间必须在 0–30,000 毫秒。")

    config = PolicyConfig(
        threshold_on=threshold_on,
        threshold_off=threshold_off,
        consecutive_required=consecutive_required,
        cooldown_ms=cooldown_ms,
        dry_run=True,
    )
    inputs = tuple(PolicyInput(**item) for item in fixture["policy_inputs"])
    decisions = run_dry_policy(inputs, config)
    external_notification_count = sum(
        decision.external_notification_sent for decision in decisions
    )
    if external_notification_count:
        raise RuntimeError("E0 dry-run 不得产生外部通知。")

    return {
        "evidence_level": "E0",
        "prediction_evidence": False,
        "deployment_approved": False,
        "dry_run": True,
        "fixture_id": fixture["fixture_id"],
        "fixture_sha256": sha256_file(FIXTURE_PATH),
        "config": asdict(config),
        "summary": {
            "decision_count": len(decisions),
            "dry_run_candidate_count": sum(
                decision.action == "RECORD_DRY_RUN_CANDIDATE"
                for decision in decisions
            ),
            "unassessable_count": sum(
                decision.state == "UNASSESSABLE" for decision in decisions
            ),
            "suppressed_count": sum(
                decision.state == "SUPPRESSED" for decision in decisions
            ),
            "external_notification_count": external_notification_count,
        },
        "decisions": [asdict(decision) for decision in decisions],
        "limitations": [
            "输入分数来自人工确定性工程夹具，不是实时手表或真实参与者数据。",
            "候选动作只记录在响应中，不振动、不发声、不通知任何人。",
            "调整阈值只能验证软件状态变化，不能产生预测有效性证据。",
        ],
    }


class WorkbenchRequestHandler(BaseHTTPRequestHandler):
    server_version = "EarlyRiskWorkbench/1.0"
    sys_version = ""

    def log_message(self, format: str, *args: object) -> None:
        super().log_message(format, *args)

    def _security_headers(self, *, content_type: str, cache_control: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        )

    def _write_bytes(
        self,
        status: HTTPStatus,
        payload: bytes,
        *,
        content_type: str,
        cache_control: str = "no-store",
        attachment_name: str | None = None,
    ) -> None:
        self.send_response(status)
        self._security_headers(content_type=content_type, cache_control=cache_control)
        if attachment_name is not None:
            self.send_header(
                "Content-Disposition", f'attachment; filename="{attachment_name}"'
            )
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _write_json(
        self, status: HTTPStatus, payload: dict[str, Any]
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self._write_bytes(
            status,
            body,
            content_type="application/json; charset=utf-8",
        )

    def _write_error(
        self,
        status: HTTPStatus,
        *,
        code: str,
        message: str,
        retryable: bool = False,
    ) -> None:
        self._write_json(
            status,
            {"error": {"code": code, "message": message, "retryable": retryable}},
        )

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path == "/" else unquote(request_path.lstrip("/"))
        if relative not in {"index.html", "app.css", "app.js", "favicon.svg", "tokens.css"}:
            self._write_error(
                HTTPStatus.NOT_FOUND,
                code="NOT_FOUND",
                message="没有找到这个工作台资源。",
            )
            return
        path = (
            PROJECT_ROOT / "frontend" / "src" / "tokens.css"
            if relative == "tokens.css"
            else WORKBENCH_ROOT / relative
        )
        if not path.is_file():
            self._write_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                code="STATIC_ASSET_MISSING",
                message="工作台静态资源不完整，请检查本地安装。",
            )
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type in {
            "application/javascript",
            "image/svg+xml",
        }:
            content_type = f"{content_type}; charset=utf-8"
        self._write_bytes(
            HTTPStatus.OK,
            path.read_bytes(),
            content_type=content_type,
            cache_control="no-cache",
        )

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        route = urlparse(self.path).path
        try:
            if route == "/api/health":
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "service": "smartwatch-risk-research-workbench",
                        "state": "ready",
                        "bind_scope": "loopback_only",
                        "evidence_level": "E0",
                        "prediction_evidence": False,
                        "public_proxy_model_ready": True,
                        "self_collected_validation_complete": False,
                        "real_world_prediction_evidence": False,
                        "deployment_approved": False,
                        "external_notifications_enabled": False,
                    },
                )
                return
            if route == "/api/workbench":
                self._write_json(HTTPStatus.OK, build_workbench_payload())
                return
            if route.startswith("/api/case-evidence/"):
                case_id = unquote(route.removeprefix("/api/case-evidence/"))
                try:
                    payload = build_case_evidence(case_id)
                except LookupError as exc:
                    self._write_error(
                        HTTPStatus.NOT_FOUND,
                        code="CASE_EVIDENCE_NOT_FOUND",
                        message=str(exc),
                    )
                    return
                self._write_json(HTTPStatus.OK, payload)
                return
            if route.startswith("/evidence/"):
                name = unquote(route.removeprefix("/evidence/"))
                path = DOWNLOADS.get(name)
                if path is None or "/" in name or "\\" in name:
                    self._write_error(
                        HTTPStatus.NOT_FOUND,
                        code="EVIDENCE_NOT_FOUND",
                        message="没有找到这个允许下载的证据文件。",
                    )
                    return
                content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                if content_type.startswith("text/") or content_type in {
                    "application/json",
                    "application/yaml",
                }:
                    content_type = f"{content_type}; charset=utf-8"
                self._write_bytes(
                    HTTPStatus.OK,
                    path.read_bytes(),
                    content_type=content_type,
                    attachment_name=name,
                )
                return
            self._serve_static(route)
        except (
            OSError,
            sqlite3.Error,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ):
            self._write_error(
                HTTPStatus.SERVICE_UNAVAILABLE,
                code="WORKBENCH_DATA_UNAVAILABLE",
                message="本机案例依据暂时无法读取，请检查数据库和案例文件后重试。",
                retryable=True,
            )

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        route = urlparse(self.path).path
        if route not in {"/api/simulate", "/api/analyze-upload"}:
            self._write_error(
                HTTPStatus.NOT_FOUND,
                code="NOT_FOUND",
                message="没有找到这个工作台操作。",
            )
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._write_error(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                code="JSON_REQUIRED",
                message="工作台请求必须使用 application/json。",
            )
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = -1
        maximum = (
            MAX_UPLOAD_REQUEST_BYTES if route == "/api/analyze-upload" else MAX_SIMULATE_REQUEST_BYTES
        )
        if content_length < 0 or content_length > maximum:
            self._write_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                code="PAYLOAD_TOO_LARGE",
                message="请求内容超过允许大小。",
            )
            return
        try:
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8")) if body else {}
            if not isinstance(payload, dict):
                raise ValueError("请求顶层必须是对象。")
            result = (
                analyze_upload_request(payload)
                if route == "/api/analyze-upload"
                else simulate_policy(payload)
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            self._write_error(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                code=(
                    "INVALID_SENSOR_FILE"
                    if route == "/api/analyze-upload"
                    else "INVALID_DRY_RUN_CONFIG"
                ),
                message=str(exc),
            )
            return
        self._write_json(HTTPStatus.OK, result)


def create_server(host: str, port: int) -> ThreadingHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("E0 工作台只允许绑定本机回环地址。")
    if not 0 <= port <= 65_535:
        raise ValueError("端口必须在 0–65535。")
    return ThreadingHTTPServer((host, port), WorkbenchRequestHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="启动仅限本机的校赛模拟手表风险评估工作台。")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8010)
    args = parser.parse_args()
    server = create_server(args.host, args.port)
    address, port = server.server_address[:2]
    print(f"模拟手表风险评估工作台已启动：http://{address}:{port}/", flush=True)
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
