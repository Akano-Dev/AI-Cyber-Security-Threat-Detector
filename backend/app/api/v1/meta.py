"""Operational metadata: GET /version and GET /metrics."""
import platform

from fastapi import APIRouter

from app.config import settings
from app.core import state
from app.core.metrics import metrics
from app.core.ws_manager import manager
from app.db import repository
from app.ml import pipeline
from app.schemas import MetricsResponse, VersionResponse

router = APIRouter(tags=["meta"])


@router.get("/version", response_model=VersionResponse, summary="Service name, version, and uptime")
def get_version():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": settings.api_version,
        "python": platform.python_version(),
        "uptime_seconds": metrics.uptime_seconds,
    }


@router.get("/metrics", response_model=MetricsResponse, summary="Runtime metrics (requests, latency, threat totals)")
def get_metrics():
    return {
        "uptime_seconds": metrics.uptime_seconds,
        "requests_total": metrics.requests_total,
        "responses_by_class": dict(metrics.responses_by_class),
        "avg_response_ms": metrics.avg_response_ms,
        "threats_total": repository.count_threats(),
        "blocked_ips": len(state.blocklist),
        "ws_clients": manager.count,
        "model_loaded": pipeline.is_ready(),
    }
