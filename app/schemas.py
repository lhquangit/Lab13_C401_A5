from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class TelemetryOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latency_ms: int | None = Field(default=None, ge=0, le=60000)
    rag_latency_ms: int | None = Field(default=None, ge=0, le=60000)
    llm_latency_ms: int | None = Field(default=None, ge=0, le=60000)
    tokens_in: int | None = Field(default=None, ge=0, le=1_000_000)
    tokens_out: int | None = Field(default=None, ge=0, le=1_000_000)
    cost_usd: float | None = Field(default=None, ge=0, le=1000)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., examples=["u_team_01"])
    session_id: str = Field(..., examples=["s_demo_01"])
    feature: str = Field(default="qa", examples=["qa", "summary"])
    message: str = Field(..., min_length=1)
    telemetry_override: TelemetryOverride | None = None
    force_error_status: int | None = Field(default=None, ge=400, le=599)
    force_error_message: str | None = Field(default=None, max_length=200)


class ChatResponse(BaseModel):
    answer: str
    correlation_id: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LogRecord(BaseModel):
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    level: Literal["info", "warning", "error", "critical"]
    service: str
    event: str
    correlation_id: str
    env: str
    user_id_hash: str | None = None
    session_id: str | None = None
    feature: str | None = None
    intent: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    cost_usd: float | None = None
    error_type: str | None = None
    tool_name: str | None = None
    payload: dict[str, Any] | None = None
