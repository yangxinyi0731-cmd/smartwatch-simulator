from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.database import SCHEMA_VERSION
from backend.app.main import create_app


def test_health_initializes_empty_database(tmp_path: Path) -> None:
    database_path = tmp_path / "health-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["event"] == "system.status"
    assert payload["service"]["state"] == "ready"
    assert payload["database"] == {
        "engine": "sqlite",
        "state": "ready",
        "schema_version": SCHEMA_VERSION,
    }
    assert payload["cases"] == {"count": 0, "state": "empty"}
    assert payload["realtime"] == {
        "transport": "websocket",
        "path": "/ws/system",
    }
    assert database_path.is_file()

    with sqlite3.connect(database_path) as connection:
        assert int(connection.execute("PRAGMA user_version").fetchone()[0]) == SCHEMA_VERSION
        assert int(connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0]) == 0


def test_websocket_publishes_current_system_status(tmp_path: Path) -> None:
    database_path = tmp_path / "websocket-test.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        with client.websocket_connect("/ws/system") as websocket:
            payload = websocket.receive_json()

    assert payload["event"] == "system.status"
    assert payload["service"]["state"] == "ready"
    assert payload["database"]["state"] == "ready"
    assert payload["cases"]["count"] == 0


def test_health_reports_sanitized_degraded_state(tmp_path: Path) -> None:
    database_path = tmp_path / "degraded.sqlite3"

    with TestClient(create_app(database_path=database_path)) as client:
        with sqlite3.connect(database_path) as connection:
            connection.execute("DROP TABLE cases")

        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["service"]["state"] == "degraded"
    assert payload["database"] == {
        "engine": "sqlite",
        "state": "unavailable",
        "schema_version": None,
    }
    assert payload["cases"] == {"count": None, "state": "unavailable"}
    assert "SQLite 数据库暂不可用" in payload["message"]
    assert "no such table" not in response.text


def test_startup_rejects_newer_database_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "future.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")

    try:
        with TestClient(create_app(database_path=database_path)):
            pass
    except RuntimeError as error:
        assert "拒绝自动降级" in str(error)
    else:
        raise AssertionError("应用不应接受高于当前程序支持版本的数据库。")
