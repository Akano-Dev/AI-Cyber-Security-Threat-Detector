"""Shared incident handling used by both /analyze and the proxy."""
from datetime import datetime, timezone

from fastapi.responses import Response

from app.config import settings
from app.core import state
from app.core.block_page import block_page
from app.core.ws_manager import manager
from app.db import repository


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


async def handle_rate_exceeded(source_ip: str) -> Response:
    """Log a brute-force event, permanently block the IP, broadcast, return 429."""
    timestamp = _now()
    payload = f">{settings.rate_limit} requests in {settings.rate_window}s"

    threat_id = repository.insert_threat(
        timestamp, source_ip, "Brute Force / Rate Abuse", payload, "high", "blocked", 99,
    )
    state.blocklist.add(source_ip)
    repository.persist_block(source_ip, timestamp)

    await manager.broadcast({
        "event": "new_threat", "id": threat_id, "timestamp": timestamp,
        "source_ip": source_ip, "threat_type": "Brute Force / Rate Abuse",
        "payload": payload, "severity": "high", "status": "blocked", "confidence": 99,
    })

    return block_page(
        429, "Too Many Requests",
        f"Your IP sent more than {settings.rate_limit} requests in "
        f"{settings.rate_window} seconds and has been permanently blocked.",
    )
