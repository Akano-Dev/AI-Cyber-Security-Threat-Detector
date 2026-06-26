"""Threat listing + block/ignore actions, CSV export, demo reset."""
import csv
import io
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core import state
from app.core.security import require_api_key
from app.core.ws_manager import manager
from app.db import repository

router = APIRouter(tags=["threats"])


@router.get("/threats")
def get_threats():
    return repository.list_threats()


async def _set_status(threat_id: int, new_status: str):
    if repository.get_threat(threat_id) is None:
        raise HTTPException(status_code=404, detail="Threat not found")
    repository.set_status(threat_id, new_status)
    await manager.broadcast({"event": "status_update", "id": threat_id, "status": new_status})
    return {"id": threat_id, "status": new_status}


@router.post("/threats/{threat_id}/block", dependencies=[Depends(require_api_key)])
async def block_threat(threat_id: int):
    threat = repository.get_threat(threat_id)
    if threat is None:
        raise HTTPException(status_code=404, detail="Threat not found")
    ip = threat["source_ip"]
    state.blocklist.add(ip)
    repository.persist_block(ip, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    return await _set_status(threat_id, "blocked")


@router.post("/threats/{threat_id}/ignore", dependencies=[Depends(require_api_key)])
async def ignore_threat(threat_id: int):
    return await _set_status(threat_id, "ignored")


@router.get("/export")
def export_report():
    rows = repository.list_threats()
    buf = io.StringIO()
    w = csv.writer(buf)

    w.writerow(["ACSTD — Threat Report", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"])
    w.writerow([])
    w.writerow(["id", "timestamp", "source_ip", "threat_type", "payload", "severity", "status", "confidence"])
    for r in rows:
        w.writerow([r["id"], r["timestamp"], r["source_ip"], r["threat_type"],
                    r["payload"], r["severity"], r["status"], r.get("confidence", "")])

    w.writerow([])
    w.writerow(["SUMMARY — By Type"])
    w.writerow(["threat_type", "count"])
    for t, c in Counter(r["threat_type"] for r in rows).most_common():
        w.writerow([t, c])

    w.writerow([])
    w.writerow(["SUMMARY — By Severity"])
    w.writerow(["severity", "count"])
    for s in ("high", "medium", "low"):
        w.writerow([s, sum(1 for r in rows if r["severity"] == s)])

    w.writerow([])
    w.writerow(["SUMMARY — By Status"])
    w.writerow(["status", "count"])
    for st, c in Counter(r["status"] for r in rows).most_common():
        w.writerow([st, c])

    buf.seek(0)
    filename = f"acstd_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        buf, media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/demo/reset", dependencies=[Depends(require_api_key)])
async def demo_reset():
    """Clear all threats and unblock all IPs — use between demo presentations."""
    repository.clear_all()
    state.blocklist.clear()
    await manager.broadcast({"event": "demo_reset"})
    return {"status": "ok", "message": "All threats cleared and all IPs unblocked."}
