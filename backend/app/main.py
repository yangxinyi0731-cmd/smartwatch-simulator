from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .config import Settings
from .database import Database
from .schemas import CaseSummary, DatabaseHealth, ServiceHealth, SystemStatus


SERVICE_VERSION = "0.2.0"
STATUS_INTERVAL_SECONDS = 15


def _build_system_status(database: Database) -> tuple[SystemStatus, int]:
    checked_at = datetime.now(UTC)
    try:
        snapshot = database.snapshot()
    except (OSError, RuntimeError, sqlite3.Error):
        return (
            SystemStatus(
                service=ServiceHealth(version=SERVICE_VERSION, state="degraded"),
                database=DatabaseHealth(state="unavailable"),
                cases=CaseSummary(count=None, state="unavailable"),
                checked_at=checked_at,
                message="后端已响应，但 SQLite 数据库暂不可用。",
            ),
            503,
        )

    return (
        SystemStatus(
            service=ServiceHealth(version=SERVICE_VERSION, state="ready"),
            database=DatabaseHealth(
                state="ready",
                schema_version=snapshot.schema_version,
            ),
            cases=CaseSummary(
                count=snapshot.case_count,
                state="empty" if snapshot.case_count == 0 else "available",
            ),
            checked_at=checked_at,
            message="本地后端与 SQLite 数据库已就绪。",
        ),
        200,
    )


def create_app(
    settings: Settings | None = None,
    *,
    database_path: Path | None = None,
) -> FastAPI:
    if settings is not None and database_path is not None:
        raise ValueError("settings 和 database_path 不能同时提供。")

    resolved_settings = settings or (
        Settings(database_path=database_path.resolve())
        if database_path is not None
        else Settings.from_environment()
    )
    database = Database(resolved_settings.database_path)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        application.state.database = database
        yield

    application = FastAPI(
        title="模拟智能手表本地服务",
        version=SERVICE_VERSION,
        description="为本地研究演示提供健康检查、SQLite 状态和实时连接。",
        lifespan=lifespan,
    )

    @application.get("/api/health", response_model=SystemStatus)
    def health(response: Response) -> SystemStatus | JSONResponse:
        status, status_code = _build_system_status(database)
        if status_code == 200:
            response.headers["Cache-Control"] = "no-store"
            return status
        return JSONResponse(
            status_code=status_code,
            content=status.model_dump(mode="json"),
            headers={"Cache-Control": "no-store"},
        )

    @application.websocket("/ws/system")
    async def system_status_socket(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                status, _ = _build_system_status(database)
                await websocket.send_json(status.model_dump(mode="json"))
                try:
                    await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=STATUS_INTERVAL_SECONDS,
                    )
                except TimeoutError:
                    continue
        except WebSocketDisconnect:
            return

    return application


app = create_app()
