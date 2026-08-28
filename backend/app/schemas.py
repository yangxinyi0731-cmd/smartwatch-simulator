from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ServiceHealth(BaseModel):
    name: str = "smartwatch-health-simulator"
    version: str
    state: Literal["ready", "degraded"]


class DatabaseHealth(BaseModel):
    engine: Literal["sqlite"] = "sqlite"
    state: Literal["ready", "unavailable"]
    schema_version: int | None = Field(default=None, ge=1)


class CaseSummary(BaseModel):
    count: int | None = Field(default=None, ge=0)
    state: Literal["empty", "available", "unavailable"]


class RealtimeHealth(BaseModel):
    transport: Literal["websocket"] = "websocket"
    path: str = "/ws/system"


class SystemStatus(BaseModel):
    event: Literal["system.status"] = "system.status"
    service: ServiceHealth
    database: DatabaseHealth
    cases: CaseSummary
    realtime: RealtimeHealth = Field(default_factory=RealtimeHealth)
    checked_at: datetime
    message: str
