"""Pydantic request/response models for the API."""
from typing import Optional

from pydantic import BaseModel, Field


# ── requests ────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    source_ip: str = Field(
        ..., max_length=64,
        description="Client IP the payload is attributed to.",
        examples=["203.0.113.5"],
    )
    payload: str = Field(
        ..., min_length=1, max_length=20_000,
        description="Raw request data (path, query, and/or body) to classify.",
        examples=["' OR '1'='1' --"],
    )
    user_agent: str = Field(
        "unknown", max_length=512,
        description="Client User-Agent string.",
        examples=["sqlmap/1.7"],
    )


class ConfigUpdate(BaseModel):
    target_url: Optional[str] = Field(
        None, max_length=2048,
        description="Proxy forward target. Empty string disables proxying.",
        examples=["http://localhost:8090"],
    )
    rate_limit: Optional[int] = Field(
        None, ge=1, le=100_000,
        description="Max requests per window before an IP is auto-blocked.",
        examples=[20],
    )
    rate_window: Optional[int] = Field(
        None, ge=1, le=86_400,
        description="Rate-limit window in seconds.",
        examples=[60],
    )


# ── responses (typed so Swagger documents them) ─────────────────────────────

class VersionResponse(BaseModel):
    name: str
    version: str
    api_version: str
    python: str
    uptime_seconds: float


class ComponentChecks(BaseModel):
    database: bool
    model_loaded: bool


class ReadinessResponse(BaseModel):
    status: str = Field(description="'ok' when all checks pass, else 'degraded'.")
    checks: ComponentChecks


class MetricsResponse(BaseModel):
    uptime_seconds: float
    requests_total: int
    responses_by_class: dict[str, int]
    avg_response_ms: float
    threats_total: int
    blocked_ips: int
    ws_clients: int
    model_loaded: bool
