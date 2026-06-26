"""GET /stats and /stats/model — summary counts and model metadata."""
from collections import Counter

from fastapi import APIRouter

from app.core import state
from app.db import repository
from app.ml import pipeline

router = APIRouter(tags=["stats"])


@router.get("/stats")
def get_stats():
    rows = repository.list_threats()
    return {
        "total": len(rows),
        "blocked_ips": len(state.blocklist),
        "by_type": dict(Counter(r["threat_type"] for r in rows)),
        "by_severity": dict(Counter(r["severity"] for r in rows)),
        "by_status": dict(Counter(r["status"] for r in rows)),
    }


@router.get("/stats/model")
def get_model_stats():
    return pipeline.model_info()
