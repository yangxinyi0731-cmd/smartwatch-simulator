from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .contracts import AgeGroup, ModelKind, TruthCategory


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ServiceHealth(ApiModel):
    name: str = "smartwatch-health-simulator"
    version: str
    state: Literal["ready", "degraded"]


class DatabaseHealth(ApiModel):
    engine: Literal["sqlite"] = "sqlite"
    state: Literal["ready", "unavailable"]
    schema_version: int | None = Field(default=None, ge=1)


class CaseSummary(ApiModel):
    count: int | None = Field(default=None, ge=0)
    state: Literal["empty", "available", "unavailable"]


class RealtimeHealth(ApiModel):
    transport: Literal["websocket"] = "websocket"
    path: str = "/ws/system"


class SystemStatus(ApiModel):
    event: Literal["system.status"] = "system.status"
    service: ServiceHealth
    database: DatabaseHealth
    cases: CaseSummary
    realtime: RealtimeHealth = Field(default_factory=RealtimeHealth)
    checked_at: datetime
    message: str


class ApiError(ApiModel):
    code: str
    message: str
    retryable: bool


class CaseListItem(ApiModel):
    case_id: str
    title: str
    truth_category: TruthCategory
    source_name: str
    fixed_version: str
    age_group: AgeGroup
    activity_label: str | None
    allowed_models: tuple[ModelKind, ...]
    sensor_stream_count: int = Field(ge=0)
    created_at: datetime


class CaseListResponse(ApiModel):
    items: tuple[CaseListItem, ...]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    @classmethod
    def from_page(
        cls,
        *,
        items: tuple[CaseListItem, ...],
        page: int,
        page_size: int,
        total: int,
    ) -> "CaseListResponse":
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )

    @model_validator(mode="after")
    def validate_page_bounds(self) -> "CaseListResponse":
        if self.total == 0:
            if self.page != 1 or self.total_pages != 0 or self.items:
                raise ValueError("空案例库必须停留在第 1 页并返回 0 页。")
        elif self.page > self.total_pages:
            raise ValueError("案例页码不能超过总页数。")
        return self
