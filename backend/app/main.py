from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from math import ceil
from pathlib import Path
from typing import Annotated, AsyncIterator, Literal

from fastapi import FastAPI, Query, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .config import Settings
from .contracts import ContractCatalog, ModelKind, TruthCategory, contract_catalog
from .database import Database
from .replay import build_replay_preview
from .reports import build_report_list
from .schemas import (
    ApiError,
    CaseListItem,
    CaseListResponse,
    CaseSummary,
    DatabaseHealth,
    ModelListItem,
    ModelListResponse,
    ReportListResponse,
    ReplayPreviewResponse,
    ServiceHealth,
    SystemStatus,
)


SERVICE_VERSION = "0.6.0"
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
        description=(
            "为本地研究演示提供健康检查、可追溯案例合同、SQLite 状态和实时连接。"
        ),
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

    @application.get("/api/contracts", response_model=ContractCatalog)
    def contracts(response: Response) -> ContractCatalog:
        response.headers["Cache-Control"] = "no-store"
        return contract_catalog()

    @application.get(
        "/api/cases",
        response_model=CaseListResponse,
        responses={
            503: {
                "model": ApiError,
                "description": "案例目录暂不可读，响应不包含内部异常。",
            }
        },
    )
    def cases(
        response: Response,
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=50)] = 20,
        query: Annotated[str | None, Query(max_length=100)] = None,
        truth_category: TruthCategory | None = None,
        model_kind: ModelKind | None = None,
        sort_by: Literal["case_id", "title", "created_at"] = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> CaseListResponse | JSONResponse:
        try:
            records, total = database.list_cases(
                page=page,
                page_size=page_size,
                query=query,
                truth_category=truth_category,
                model_kind=model_kind,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            total_pages = ceil(total / page_size) if total else 0
            resolved_page = min(page, total_pages) if total_pages else 1
            if resolved_page != page:
                records, total = database.list_cases(
                    page=resolved_page,
                    page_size=page_size,
                    query=query,
                    truth_category=truth_category,
                    model_kind=model_kind,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
        except (OSError, RuntimeError, sqlite3.Error):
            error = ApiError(
                code="CASE_CATALOG_UNAVAILABLE",
                message="案例库暂不可用，请稍后重试。",
                retryable=True,
            )
            return JSONResponse(
                status_code=503,
                content=error.model_dump(mode="json"),
                headers={"Cache-Control": "no-store"},
            )

        response.headers["Cache-Control"] = "no-store"
        items = tuple(
            CaseListItem(
                case_id=record.case_id,
                title=record.title,
                truth_category=record.truth_category,
                source_name=record.source_name,
                fixed_version=record.fixed_version,
                age_group=record.age_group,
                activity_label=record.activity_label,
                allowed_models=record.allowed_models,
                sensor_stream_count=record.sensor_stream_count,
                created_at=record.created_at,
            )
            for record in records
        )
        return CaseListResponse.from_page(
            items=items,
            page=resolved_page,
            page_size=page_size,
            total=total,
        )

    @application.get(
        "/api/models",
        response_model=ModelListResponse,
        responses={
            503: {
                "model": ApiError,
                "description": "模型清单暂不可读，响应不包含内部异常。",
            }
        },
    )
    def models(response: Response) -> ModelListResponse | JSONResponse:
        try:
            records = database.list_model_manifests()
        except (OSError, RuntimeError, sqlite3.Error, ValueError, KeyError):
            error = ApiError(
                code="MODEL_CATALOG_UNAVAILABLE",
                message="模型清单暂不可用，请稍后重试。",
                retryable=True,
            )
            return JSONResponse(
                status_code=503,
                content=error.model_dump(mode="json"),
                headers={"Cache-Control": "no-store"},
            )

        response.headers["Cache-Control"] = "no-store"
        items = tuple(
            ModelListItem(
                manifest_id=record.manifest_id,
                model_id=record.model_id,
                model_kind=record.model_kind,
                version=record.version,
                format=record.format,
                source_commit=record.source_commit,
                artifact_relative_path=record.artifact_relative_path,
                artifact_sha256=record.artifact_sha256,
                training_truth_categories=record.training_truth_categories,
                evaluation_reference=record.evaluation_reference,
                limitations=record.limitations,
                deployment_approved=record.deployment_approved,
                approval_status=record.approval_status,
                external_validation_completed=record.external_validation_completed,
                created_at=record.created_at,
            )
            for record in records
        )
        return ModelListResponse(items=items, total=len(items))

    @application.get(
        "/api/reports",
        response_model=ReportListResponse,
        responses={
            503: {
                "model": ApiError,
                "description": "评估报告暂不可读，响应不包含内部异常。",
            }
        },
    )
    def reports(response: Response) -> ReportListResponse | JSONResponse:
        try:
            result = build_report_list(database.list_model_manifests())
        except (OSError, RuntimeError, sqlite3.Error, ValueError, KeyError, TypeError, json.JSONDecodeError):
            error = ApiError(
                code="REPORT_CATALOG_UNAVAILABLE",
                message="测试报告暂不可用，请核对本地报告文件后重试。",
                retryable=True,
            )
            return JSONResponse(
                status_code=503,
                content=error.model_dump(mode="json"),
                headers={"Cache-Control": "no-store"},
            )
        response.headers["Cache-Control"] = "no-store"
        return result

    @application.get(
        "/api/reports/export.json",
        response_model=ReportListResponse,
        responses={503: {"model": ApiError, "description": "评估报告暂不可导出。"}},
    )
    def export_reports() -> JSONResponse:
        try:
            result = build_report_list(database.list_model_manifests())
        except (OSError, RuntimeError, sqlite3.Error, ValueError, KeyError, TypeError, json.JSONDecodeError):
            error = ApiError(
                code="REPORT_EXPORT_UNAVAILABLE",
                message="测试报告暂不可导出，请核对本地报告文件后重试。",
                retryable=True,
            )
            return JSONResponse(
                status_code=503,
                content=error.model_dump(mode="json"),
                headers={"Cache-Control": "no-store"},
            )
        return JSONResponse(
            content=result.model_dump(mode="json"),
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": (
                    'attachment; filename="smartwatch-model-evaluation-reports.json"'
                ),
            },
        )

    @application.get(
        "/api/cases/{case_id}/replay-preview",
        response_model=ReplayPreviewResponse,
        responses={
            404: {"model": ApiError, "description": "案例不存在。"},
            503: {
                "model": ApiError,
                "description": "案例回放数据暂不可读，响应不包含内部异常。",
            },
        },
    )
    def replay_preview(
        case_id: str,
        response: Response,
    ) -> ReplayPreviewResponse | JSONResponse:
        try:
            bundle = database.get_case_runtime_bundle(case_id)
            if bundle is None:
                error = ApiError(
                    code="CASE_NOT_FOUND",
                    message="没有找到这个测试案例。",
                    retryable=False,
                )
                return JSONResponse(
                    status_code=404,
                    content=error.model_dump(mode="json"),
                    headers={"Cache-Control": "no-store"},
                )
            preview = build_replay_preview(bundle)
        except (OSError, RuntimeError, sqlite3.Error, ValueError, KeyError):
            error = ApiError(
                code="REPLAY_PREVIEW_UNAVAILABLE",
                message="案例回放数据暂不可用，请核对本地文件后重试。",
                retryable=True,
            )
            return JSONResponse(
                status_code=503,
                content=error.model_dump(mode="json"),
                headers={"Cache-Control": "no-store"},
            )
        response.headers["Cache-Control"] = "no-store"
        return preview

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
