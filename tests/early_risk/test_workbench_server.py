from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from typing import Iterator
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from research.early_risk.workbench_server import (
    build_workbench_payload,
    create_server,
    simulate_policy,
)


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


def test_policy_simulation_is_deterministic_and_never_notifies() -> None:
    first = simulate_policy({})
    second = simulate_policy({})

    assert first == second
    assert first["dry_run"] is True
    assert first["prediction_evidence"] is False
    assert first["summary"]["decision_count"] == 7
    assert first["summary"]["external_notification_count"] == 0
    assert not any(item["external_notification_sent"] for item in first["decisions"])


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
        assert health_headers["Cache-Control"] == "no-store"
        assert health_headers["X-Frame-Options"] == "DENY"
        assert "default-src 'self'" in health_headers["Content-Security-Policy"]

        dashboard, _ = read_json(f"{base_url}/api/workbench")
        assert dashboard["gate"]["p2"]["external_notification_count"] == 0

        with urlopen(f"{base_url}/", timeout=5) as response:  # noqa: S310
            html = response.read().decode("utf-8")
            assert "先认识每位老人的平常" in html
            assert "老人一天的生活路线" in html
            assert "快速坐到沙发" in html
            assert "摘表充电" in html
            assert "只演示，不报警" in html
            assert response.headers["X-Content-Type-Options"] == "nosniff"

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
