from __future__ import annotations

import json
import threading
import base64
from contextlib import contextmanager
from typing import Iterator
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from research.early_risk.workbench_server import (
    _downsample_indices,
    build_case_evidence,
    build_workbench_payload,
    create_server,
    simulate_policy,
)
from research.early_risk.public_risk_model import PublicEarlyRiskModel
from research.early_risk.train_public_risk_baseline import (
    ARTIFACT_PATH,
    CALIBRATION_PARTICIPANTS,
    EVALUATION_PARTICIPANTS,
    REPORT_PATH,
    TRAIN_PARTICIPANTS,
    build_examples,
)
from research.early_risk.upload_analysis import analyze_upload_request


@contextmanager
def running_workbench() -> Iterator[str]:
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def read_json(url: str) -> tuple[dict[str, object], object]:
    with urlopen(url, timeout=5) as response:  # noqa: S310 - loopback test server
        return json.load(response), response.headers


def test_workbench_payload_preserves_e0_truth_boundary() -> None:
    payload = build_workbench_payload()

    assert payload["meta"]["evidence_level"] == "E0"
    assert payload["meta"]["prediction_evidence"] is False
    assert payload["meta"]["public_proxy_model_ready"] is True
    assert payload["meta"]["real_world_prediction_evidence"] is False
    assert payload["meta"]["self_collected_validation_complete"] is True
    assert payload["meta"]["deployment_approved"] is False
    assert payload["meta"]["next_stage_authorized"] is False
    assert len(payload["pipeline"]) == 10
    assert [item["state"] for item in payload["pipeline"][:3]] == [
        "engineering_pass",
        "engineering_pass",
        "engineering_pass",
    ]
    assert all(item["state"] == "locked" for item in payload["pipeline"][3:])
    assert payload["audit"]["audited_asset_count"] == 11
    assert payload["audit"]["no_download_performed"] is True
    assert payload["public_risk_model"]["status"] == "PUBLIC_PROXY_BASELINE_READY"
    assert payload["public_risk_model"]["participant_disjoint"] is True
    assert payload["self_collected"]["received_case_count"] == 30
    assert payload["self_collected"]["accepted_case_count"] == 30
    assert payload["self_collected"]["claim_enabled"] is True
    assert len(payload["self_collected"]["cases"]) == 30


def test_public_proxy_model_is_causal_monotonic_and_participant_disjoint() -> None:
    feature_names, examples = build_examples()
    assert feature_names
    assert examples
    assert all(item.anchor_sample is None or item.end_sample < item.anchor_sample for item in examples)

    train = set(TRAIN_PARTICIPANTS)
    calibration = set(CALIBRATION_PARTICIPANTS)
    evaluation = set(EVALUATION_PARTICIPANTS)
    assert not train & calibration
    assert not train & evaluation
    assert not calibration & evaluation

    model = PublicEarlyRiskModel(ARTIFACT_PATH)
    sample = next(item for item in examples if item.participant_id in evaluation)
    probabilities = model.predict_feature_matrix(sample.features[None, :])
    assert probabilities.shape == (1, 3)
    assert 0 <= probabilities[0, 0] <= probabilities[0, 1] <= probabilities[0, 2] <= 1

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    assert report["proxy_anchor"]["is_adjudicated_t_instability"] is False
    assert report["leakage_controls"]["post_anchor_samples_used"] is False
    assert report["self_collected_engineering_validation"]["received_case_count"] == 0
    assert report["evaluation_snapshot_at_exact_lead"]["3"]["eligible_simulated_fall_count"] >= 8


def _stationary_csv(sample_count: int = 250) -> bytes:
    rows = ["time_s,ax,ay,az,gx,gy,gz"]
    rows.extend(
        f"{index / 50:.2f},0.0,0.0,9.80665,0.0,0.0,0.0"
        for index in range(sample_count)
    )
    return ("\n".join(rows) + "\n").encode("utf-8")


def test_new_data_analysis_runs_real_models_without_persisting_upload() -> None:
    content = _stationary_csv()
    result = analyze_upload_request(
        {
            "file_name": "manual-test.csv",
            "content_base64": base64.b64encode(content).decode("ascii"),
            "acceleration_unit": "m/s2",
            "gyroscope_unit": "rad/s",
        }
    )

    assert result["file"]["persisted"] is False
    assert result["quality"]["normalized_rate_hz"] == 50.0
    assert result["analysis"]["fall_model"]["status"] == "COMPLETED"
    assert result["analysis"]["early_risk_model"]["status"] == "COMPLETED"
    assert len(result["analysis"]["early_risk_model"]["timeline"]) > 1
    assert result["analysis"]["activity_model"]["status"] == "INSUFFICIENT_DURATION"
    assert [item["id"] for item in result["pipeline"]] == [
        "validate",
        "normalize",
        "activity",
        "fall",
        "risk",
        "explain",
    ]
    assert all(item["detail"] for item in result["pipeline"])
    interpretation = result["analysis"]["interpretation"]
    assert len(interpretation["model_reasoning"]) == 3
    assert "不会相加" in interpretation["decision_rule"]
    assert interpretation["scope_note"]
    assert result["truth_boundary"]["self_collected_validation_complete"] is False
    assert result["truth_boundary"]["external_notification_sent"] is False


def test_new_data_analysis_rejects_missing_gyroscope_columns() -> None:
    content = b"time_s,ax,ay,az\n0,0,0,9.8\n"
    with pytest.raises(ValueError, match="表头"):
        analyze_upload_request(
            {
                "file_name": "missing-gyro.csv",
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        )


def test_policy_simulation_is_deterministic_and_never_notifies() -> None:
    first = simulate_policy({})
    second = simulate_policy({})

    assert first == second
    assert first["dry_run"] is True
    assert first["prediction_evidence"] is False
    assert first["summary"]["decision_count"] == 7
    assert first["summary"]["external_notification_count"] == 0
    assert not any(item["external_notification_sent"] for item in first["decisions"])


def test_case_evidence_downsampling_is_bounded_and_keeps_last_sample() -> None:
    indices = _downsample_indices(631, (217, 408))

    assert indices[0] == 0
    assert indices[-1] == 630
    assert 217 in indices
    assert 408 in indices
    assert len(indices) <= 241
    assert tuple(sorted(set(indices))) == indices


def test_routine_evidence_uses_fixed_events_instead_of_fake_waveform() -> None:
    evidence = build_case_evidence("synthetic-routine-100-v1")

    assert evidence["evidence_type"] == "synthetic_routine_timeline"
    assert evidence["content_verified"] is True
    assert evidence["profile"]["history_days"] == 100
    assert evidence["profile"]["event_count"] == 551
    assert evidence["profile"]["displayed_day_count"] == 14
    assert len(evidence["days"]) == 14
    assert [item["id"] for item in evidence["pipeline"]] == [
        "validate",
        "normalize",
        "activity",
        "fall",
        "risk",
        "explain",
    ]
    assert evidence["analysis"]["routine_model"]["status"] == "COMPLETED"
    assert evidence["analysis"]["fall_model"]["status"] == "NOT_APPLICABLE"
    assert evidence["analysis"]["early_risk_model"]["status"] == "NOT_APPLICABLE"
    assert len(evidence["analysis"]["interpretation"]["model_reasoning"]) == 3
    assert "不伪造波形" in " ".join(evidence["limitations"])


def test_public_sensor_cases_share_pipeline_and_run_only_applicable_models() -> None:
    fall = build_case_evidence("weda-f01-u01_r01")
    activity = build_case_evidence("capture24-walking-p123")
    expected_steps = ["validate", "normalize", "activity", "fall", "risk", "explain"]

    assert [item["id"] for item in fall["pipeline"]] == expected_steps
    assert [item["id"] for item in activity["pipeline"]] == expected_steps
    assert fall["analysis"]["fall_model"]["status"] == "COMPLETED"
    assert fall["analysis"]["early_risk_model"]["status"] == "COMPLETED"
    assert activity["analysis"]["activity_model"]["status"] == "COMPLETED"
    assert activity["analysis"]["fall_model"]["status"] == "NOT_APPLICABLE"
    assert activity["analysis"]["early_risk_model"]["status"] == "NOT_APPLICABLE"
    assert activity["analysis"]["activity_model"]["probabilities"]
    assert "未运行不等于" in activity["analysis"]["interpretation"]["decision_rule"]


@pytest.mark.parametrize(
    "payload",
    [
        {"dry_run": False},
        {"threshold_on": 0.5},
        {"threshold_on": 0.8, "threshold_off": 0.8},
        {"consecutive_required": 0},
        {"cooldown_ms": 30_001},
        {"threshold_on": "0.8"},
        {"consecutive_required": 2.7},
        {"consecutive_required": True},
        {"cooldown_ms": 5_000.5},
    ],
)
def test_policy_simulation_rejects_unsafe_or_invalid_configuration(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        simulate_policy(payload)


def test_server_refuses_non_loopback_binding() -> None:
    with pytest.raises(ValueError, match="回环地址"):
        create_server("0.0.0.0", 0)


def test_http_surface_serves_public_life_context_and_safe_demo() -> None:
    with running_workbench() as base_url:
        health, health_headers = read_json(f"{base_url}/api/health")
        assert health["state"] == "ready"
        assert health["bind_scope"] == "loopback_only"
        assert health["external_notifications_enabled"] is False
        assert health["public_proxy_model_ready"] is True
        assert health["self_collected_validation_complete"] is True
        assert health_headers["Cache-Control"] == "no-store"
        assert health_headers["X-Frame-Options"] == "DENY"
        assert "default-src 'self'" in health_headers["Content-Security-Policy"]

        dashboard, _ = read_json(f"{base_url}/api/workbench")
        assert dashboard["gate"]["p2"]["external_notification_count"] == 0

        with urlopen(f"{base_url}/", timeout=5) as response:  # noqa: S310
            html = response.read().decode("utf-8")
            assert "选择文件，运行整条判断链路" in html
            assert "自主采集 30 / 约30组" in html
            assert "1 / 2 / 3 秒研究分数" in html
            assert "逐秒风险变化" in html
            assert "加速度与腕部转动变化" in html
            assert "操作模拟手表" in html
            assert "跌倒特征匹配度" in html
            assert "结果分析" in html
            assert "共用六步判断流程" in html
            assert "各模型如何参与判断" in html
            assert "只有数据来源不同" in html
            assert "动作示意、实际信号与规则对照" in html
            assert "示意图不作为判断证据" in html
            assert "格式化判断依据" in html
            assert "判断连续腕部动作是否与受控跌倒动作相似" in html
            assert "参与者受控模拟跌倒" in html
            assert "后端尚未接入" not in html
            assert "年轻参与者" not in html
            assert "真实老人" not in html
            assert response.headers["X-Content-Type-Options"] == "nosniff"

        with urlopen(f"{base_url}/app.js", timeout=5) as response:  # noqa: S310
            script = response.read().decode("utf-8")
            assert "ANALYSIS_PIPELINE_STEPS" in script
            assert "检查输入数据" in script
            assert "模型结果分开计算" in script
            assert "需要复核" in script
            assert "不是现实跌倒概率" in script
            assert "/api/case-evidence/" in script
            assert "renderSensorChart" in script
            assert "renderRoutineChart" in script
            assert "renderRiskChart" in script
            assert "/api/analyze-upload" in script
            assert "年轻参与者" not in script
            assert "真实老人" not in script

        routine_evidence, _ = read_json(
            f"{base_url}/api/case-evidence/synthetic-routine-100-v1"
        )
        assert routine_evidence["evidence_type"] == "synthetic_routine_timeline"
        assert routine_evidence["profile"]["event_count"] == 551

        request = Request(
            f"{base_url}/api/simulate",
            data=json.dumps(
                {
                    "threshold_on": 0.85,
                    "threshold_off": 0.4,
                    "consecutive_required": 2,
                    "cooldown_ms": 5_000,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:  # noqa: S310
            simulation = json.load(response)
        assert simulation["dry_run"] is True
        assert simulation["summary"]["external_notification_count"] == 0

        upload_request = Request(
            f"{base_url}/api/analyze-upload",
            data=json.dumps(
                {
                    "file_name": "manual-test.csv",
                    "content_base64": base64.b64encode(_stationary_csv()).decode("ascii"),
                    "acceleration_unit": "m/s2",
                    "gyroscope_unit": "rad/s",
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(upload_request, timeout=15) as response:  # noqa: S310
            upload = json.load(response)
        assert upload["file"]["persisted"] is False
        assert upload["analysis"]["early_risk_model"]["status"] == "COMPLETED"

        with urlopen(f"{base_url}/evidence/gate-summary.json", timeout=5) as response:  # noqa: S310
            evidence = json.load(response)
            assert evidence["evidence_level"] == "E0"
            assert response.headers["Content-Disposition"].startswith("attachment;")


def test_http_surface_rejects_path_traversal_and_non_json_posts() -> None:
    with running_workbench() as base_url:
        with pytest.raises(HTTPError) as traversal_error:
            urlopen(  # noqa: S310 - loopback test server
                f"{base_url}/evidence/%2E%2E%2Ftarget-contract.yaml", timeout=5
            )
        assert traversal_error.value.code == 404

        with pytest.raises(HTTPError) as case_traversal_error:
            urlopen(  # noqa: S310 - loopback test server
                f"{base_url}/api/case-evidence/%2E%2E%2Fsmartwatch.sqlite3",
                timeout=5,
            )
        assert case_traversal_error.value.code == 404

        request = Request(
            f"{base_url}/api/simulate",
            data=b"threshold_on=0.8",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with pytest.raises(HTTPError) as media_error:
            urlopen(request, timeout=5)  # noqa: S310 - loopback test server
        assert media_error.value.code == 415

        oversized_request = Request(
            f"{base_url}/api/simulate",
            data=b"{" + (b" " * (16 * 1024)) + b"}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as oversized_error:
            urlopen(oversized_request, timeout=5)  # noqa: S310 - loopback test server
        assert oversized_error.value.code == 413
