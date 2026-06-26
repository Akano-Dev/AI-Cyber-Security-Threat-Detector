"""Inline inspecting proxy: block threats, forward safe traffic to TARGET_URL."""
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.config import forward_base
from app.core import state
from app.core.block_page import block_page
from app.core.incidents import handle_rate_exceeded
from app.core.logging import logger
from app.core.rate_limit import rate_limiter
from app.core.security import get_client_ip
from app.core.ws_manager import manager
from app.db import repository
from app.detection import engine

router = APIRouter(tags=["proxy"])

_LOCALHOST = {"127.0.0.1", "::1", "localhost"}
_SKIP_HEADERS = {"host", "content-length", "transfer-encoding", "connection"}


@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str):
    source_ip = get_client_ip(request)

    if source_ip in state.blocklist:
        return block_page(403, "Your IP is Blocked",
                          "This IP address has been flagged and blocked by the security system.")

    if rate_limiter.is_exceeded(source_ip):
        return await handle_rate_exceeded(source_ip)

    body_bytes = await request.body()
    body_text = body_bytes.decode("utf-8", errors="replace")
    query = str(request.url.query)
    payload = " ".join(filter(None, [path, query, body_text])) or "/"
    user_agent = request.headers.get("user-agent", "unknown")

    threat_type, severity, confidence = engine.evaluate(payload, user_agent)

    if threat_type:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        auto_blocked = severity == "high" and source_ip not in _LOCALHOST
        initial_status = "blocked" if auto_blocked else "new"

        if auto_blocked:
            state.blocklist.add(source_ip)
            repository.persist_block(source_ip, timestamp)

        threat_id = repository.insert_threat(
            timestamp, source_ip, threat_type, payload[:500], severity, initial_status, confidence,
        )
        await manager.broadcast({
            "event": "new_threat", "id": threat_id, "timestamp": timestamp,
            "source_ip": source_ip, "threat_type": threat_type, "payload": payload[:500],
            "severity": severity, "status": initial_status, "confidence": confidence,
        })

        return block_page(403, "Threat Detected",
                          f"A <strong>{threat_type}</strong> attack was identified in your request. Access has been denied.")

    # Safe — forward to the configured target.
    target = forward_base()
    if not target:
        return block_page(502, "Proxy Not Configured",
                          "No target URL is set. Open the dashboard and configure a Target URL in Proxy Settings.")

    forward_url = f"{target}/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _SKIP_HEADERS}

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.request(
                method=request.method, url=forward_url, headers=headers,
                content=body_bytes, params=dict(request.query_params),
            )
    except httpx.RequestError as exc:
        logger.warning("Proxy forward to %s failed: %s", forward_url, exc)
        return block_page(502, "Upstream Unreachable",
                          "The protected site could not be reached. Please try again later.")

    return Response(
        content=resp.content, status_code=resp.status_code,
        headers=dict(resp.headers), media_type=resp.headers.get("content-type"),
    )
