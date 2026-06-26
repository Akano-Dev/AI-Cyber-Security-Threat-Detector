"""POST /analyze — classify a single payload (used by the dashboard + simulator)."""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.core import state
from app.core.incidents import handle_rate_exceeded
from app.core.rate_limit import rate_limiter
from app.core.ws_manager import manager
from app.db import repository
from app.detection import engine
from app.schemas import AnalyzeRequest

router = APIRouter(tags=["detection"])


@router.post("/analyze")
async def post_analyze(req: AnalyzeRequest):
    if req.source_ip in state.blocklist:
        return {"verdict": "blocked", "source_ip": req.source_ip}

    if rate_limiter.is_exceeded(req.source_ip):
        await handle_rate_exceeded(req.source_ip)
        return {"verdict": "blocked", "source_ip": req.source_ip, "reason": "rate_limit"}

    threat_type, severity, confidence = engine.evaluate(req.payload, req.user_agent)
    if threat_type is None:
        return {"verdict": "safe"}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    threat_id = repository.insert_threat(
        timestamp, req.source_ip, threat_type, req.payload, severity, "new", confidence,
    )

    threat = {
        "event": "new_threat", "id": threat_id, "timestamp": timestamp,
        "source_ip": req.source_ip, "threat_type": threat_type, "payload": req.payload,
        "severity": severity, "status": "new", "confidence": confidence,
    }
    await manager.broadcast(threat)

    return {"verdict": "threat", **{k: v for k, v in threat.items() if k != "event"}}
