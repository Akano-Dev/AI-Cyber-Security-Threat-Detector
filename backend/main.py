import asyncio
import csv
import io
import json
import os
from collections import Counter, defaultdict
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from database import init_db, get_conn, load_blocked_ips, persist_block, remove_block
from detection import analyze
import ml_model

load_dotenv()
TARGET_URL  = os.getenv("TARGET_URL", "").rstrip("/")
RATE_LIMIT  = int(os.getenv("RATE_LIMIT", "20"))
RATE_WINDOW = int(os.getenv("RATE_WINDOW", "60"))

ENV_PATH = Path(__file__).parent / ".env"


def _write_env(updates: dict):
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    result, seen = [], set()
    for line in lines:
        key = line.split("=")[0].strip() if "=" in line and not line.startswith("#") else ""
        if key in updates:
            result.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            result.append(line)
    for k, v in updates.items():
        if k not in seen:
            result.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(result) + "\n", encoding="utf-8")

blocklist: set[str] = set()


class RateLimiter:
    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)

    def is_exceeded(self, ip: str) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        dq  = self._hits[ip]
        while dq and dq[0] < now - RATE_WINDOW:
            dq.popleft()
        dq.append(now)
        return len(dq) > RATE_LIMIT

rate_limiter = RateLimiter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    blocklist.update(load_blocked_ips())
    loaded = ml_model.load_model()
    print(f"Loaded {len(blocklist)} blocked IP(s) from database.")
    print("ML model loaded." if loaded else "WARNING: model.pkl not found — run python train.py first.")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket connection manager ---

class ConnectionManager:
    def __init__(self):
        self._clients: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._clients.append(ws)

    def disconnect(self, ws: WebSocket):
        self._clients.remove(ws)

    async def broadcast(self, data: dict):
        message = json.dumps(data)
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:
                self._clients.remove(ws)

manager = ConnectionManager()


# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/threats")
def get_threats():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM threats ORDER BY timestamp DESC"
        ).fetchall()
    return [dict(row) for row in rows]


class AnalyzeRequest(BaseModel):
    source_ip: str
    payload: str
    user_agent: str = "unknown"


async def _handle_rate_exceeded(source_ip: str) -> Response:
    """Log brute-force, auto-block the IP, and return 429."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO threats (timestamp, source_ip, threat_type, payload, severity, status, confidence) VALUES (?,?,?,?,?,?,?)",
            (timestamp, source_ip, "Brute Force / Rate Abuse", f">{RATE_LIMIT} requests in {RATE_WINDOW}s", "high", "blocked", 99),
        )
        threat_id = cur.lastrowid

    blocklist.add(source_ip)
    persist_block(source_ip, timestamp)

    await manager.broadcast({
        "event": "new_threat", "id": threat_id, "timestamp": timestamp,
        "source_ip": source_ip, "threat_type": "Brute Force / Rate Abuse",
        "payload": f">{RATE_LIMIT} requests in {RATE_WINDOW}s",
        "severity": "high", "status": "blocked", "confidence": 99,
    })

    return _block_page(429, "Too Many Requests",
                       f"Your IP sent more than {RATE_LIMIT} requests in {RATE_WINDOW} seconds and has been permanently blocked.")


def _block_page(status: int, title: str, detail: str) -> Response:
    color = "#ef4444" if status == 403 else "#f59e0b"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{status} — Blocked</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #050c18;
      background-image:
        linear-gradient(rgba(6,182,212,.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(6,182,212,.04) 1px, transparent 1px);
      background-size: 40px 40px;
      font-family: system-ui, sans-serif;
      color: #f1f5f9;
    }}
    .card {{
      background: #0c1520;
      border: 1px solid #1a2d45;
      border-radius: 20px;
      padding: 48px 56px;
      max-width: 480px;
      width: 90%;
      text-align: center;
      box-shadow: 0 0 60px rgba(6,182,212,.05);
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: {color}18;
      color: {color};
      border: 1px solid {color}30;
      border-radius: 999px;
      padding: 6px 16px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
      margin-bottom: 24px;
    }}
    .dot {{
      width: 7px; height: 7px;
      background: {color};
      border-radius: 50%;
      animation: pulse 1.8s ease-in-out infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50%        {{ opacity: .4; transform: scale(1.5); }}
    }}
    h1 {{
      font-size: 56px;
      font-weight: 800;
      color: {color};
      letter-spacing: -.02em;
      line-height: 1;
      margin-bottom: 12px;
    }}
    h2 {{
      font-size: 18px;
      font-weight: 600;
      color: #e2e8f0;
      margin-bottom: 12px;
    }}
    p {{
      font-size: 14px;
      color: #64748b;
      line-height: 1.6;
    }}
    .divider {{
      border: none;
      border-top: 1px solid #1a2d45;
      margin: 28px 0;
    }}
    .brand {{
      font-size: 12px;
      color: #334155;
      letter-spacing: .06em;
    }}
    .brand span {{ color: #06b6d4; font-weight: 700; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="badge"><span class="dot"></span>Access Denied</div>
    <h1>{status}</h1>
    <h2>{title}</h2>
    <p>{detail}</p>
    <hr class="divider" />
    <p class="brand">Protected by <span>ACSTD</span> · AI Cyber Security Threat Detector</p>
  </div>
</body>
</html>"""
    return Response(content=html, status_code=status, media_type="text/html")


def _combined_verdict(sig_result, ml_prob: float):
    """Combine signature rules + ML probability into (threat_type, severity, confidence_pct | None)."""
    ml_pct = round(ml_prob * 100)

    if sig_result:
        # Signature is authoritative; ML boosts or tempers confidence
        confidence = max(ml_pct, 65) if ml_prob >= 0.5 else 65
        return sig_result["threat_type"], sig_result["severity"], confidence

    if ml_prob >= 0.70:
        # ML-only detection
        return "Anomalous Payload", "medium", ml_pct

    return None, None, None


@app.post("/analyze")
async def post_analyze(req: AnalyzeRequest):
    if req.source_ip in blocklist:
        return {"verdict": "blocked", "source_ip": req.source_ip}

    if rate_limiter.is_exceeded(req.source_ip):
        await _handle_rate_exceeded(req.source_ip)
        return {"verdict": "blocked", "source_ip": req.source_ip, "reason": "rate_limit"}

    sig_result = analyze(req.payload, req.user_agent)
    ml_prob    = ml_model.predict(req.payload)
    threat_type, severity, confidence = _combined_verdict(sig_result, ml_prob)

    if threat_type is None:
        return {"verdict": "safe"}

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO threats (timestamp, source_ip, threat_type, payload, severity, status, confidence) VALUES (?,?,?,?,?,?,?)",
            (timestamp, req.source_ip, threat_type, req.payload, severity, "new", confidence),
        )
        threat_id = cur.lastrowid

    threat = {
        "event":       "new_threat",
        "id":          threat_id,
        "timestamp":   timestamp,
        "source_ip":   req.source_ip,
        "threat_type": threat_type,
        "payload":     req.payload,
        "severity":    severity,
        "status":      "new",
        "confidence":  confidence,
    }

    await manager.broadcast(threat)

    return {"verdict": "threat", **{k: v for k, v in threat.items() if k != "event"}}


async def _set_status(threat_id: int, new_status: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM threats WHERE id = ?", (threat_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Threat not found")
        conn.execute("UPDATE threats SET status = ? WHERE id = ?", (new_status, threat_id))

    await manager.broadcast({"event": "status_update", "id": threat_id, "status": new_status})
    return {"id": threat_id, "status": new_status}


@app.post("/threats/{threat_id}/block")
async def block_threat(threat_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT source_ip FROM threats WHERE id = ?", (threat_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Threat not found")
        ip = row["source_ip"]
    blocklist.add(ip)
    persist_block(ip, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    return await _set_status(threat_id, "blocked")


@app.post("/threats/{threat_id}/ignore")
async def ignore_threat(threat_id: int):
    return await _set_status(threat_id, "ignored")


class ConfigUpdate(BaseModel):
    target_url: Optional[str] = None
    rate_limit: Optional[int] = None
    rate_window: Optional[int] = None


@app.get("/config")
def get_config():
    return {"target_url": TARGET_URL, "rate_limit": RATE_LIMIT, "rate_window": RATE_WINDOW}


@app.post("/config")
def update_config(cfg: ConfigUpdate):
    global TARGET_URL, RATE_LIMIT, RATE_WINDOW
    updates = {}
    if cfg.target_url is not None:
        TARGET_URL = cfg.target_url.rstrip("/")
        updates["TARGET_URL"] = cfg.target_url
    if cfg.rate_limit is not None:
        RATE_LIMIT = cfg.rate_limit
        updates["RATE_LIMIT"] = str(cfg.rate_limit)
    if cfg.rate_window is not None:
        RATE_WINDOW = cfg.rate_window
        updates["RATE_WINDOW"] = str(cfg.rate_window)
    _write_env(updates)
    return {"target_url": TARGET_URL, "rate_limit": RATE_LIMIT, "rate_window": RATE_WINDOW}


@app.get("/export")
def export_report():
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT * FROM threats ORDER BY timestamp DESC"
        ).fetchall()]

    buf = io.StringIO()
    w = csv.writer(buf)

    # ── Threat log ──────────────────────────────────────────────────────────
    w.writerow(["ACSTD — Threat Report", f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC"])
    w.writerow([])
    w.writerow(["id", "timestamp", "source_ip", "threat_type", "payload", "severity", "status", "confidence"])
    for r in rows:
        w.writerow([r["id"], r["timestamp"], r["source_ip"], r["threat_type"],
                    r["payload"], r["severity"], r["status"], r.get("confidence", "")])

    # ── Summary ─────────────────────────────────────────────────────────────
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
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/demo/reset")
async def demo_reset():
    """Clear all threats and unblock all IPs — use between demo presentations."""
    with get_conn() as conn:
        conn.execute("DELETE FROM threats")
        conn.execute("DELETE FROM blocked_ips")
    blocklist.clear()
    await manager.broadcast({"event": "demo_reset"})
    return {"status": "ok", "message": "All threats cleared and all IPs unblocked."}


@app.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str):
    """Inspect every request, block threats, forward safe ones to TARGET_URL."""
    source_ip = request.client.host

    # Blocked IP — reject immediately
    if source_ip in blocklist:
        return _block_page(403, "Your IP is Blocked",
                           "This IP address has been flagged and blocked by the security system.")

    # Rate limit check
    if rate_limiter.is_exceeded(source_ip):
        return await _handle_rate_exceeded(source_ip)

    # Build payload string to analyze (path + query + body)
    body_bytes = await request.body()
    body_text  = body_bytes.decode("utf-8", errors="replace")
    query      = str(request.url.query)
    payload    = " ".join(filter(None, [path, query, body_text])) or "/"
    user_agent = request.headers.get("user-agent", "unknown")

    sig_result = analyze(payload, user_agent)
    ml_prob    = ml_model.predict(payload)
    threat_type, severity, confidence = _combined_verdict(sig_result, ml_prob)

    if threat_type:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Auto-block high severity (skip localhost so demo presentations aren't locked out)
        _localhost = {"127.0.0.1", "::1", "localhost"}
        auto_blocked = severity == "high" and source_ip not in _localhost
        initial_status = "blocked" if auto_blocked else "new"

        if auto_blocked:
            blocklist.add(source_ip)
            persist_block(source_ip, timestamp)

        with get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO threats (timestamp, source_ip, threat_type, payload, severity, status, confidence) VALUES (?,?,?,?,?,?,?)",
                (timestamp, source_ip, threat_type, payload[:500], severity, initial_status, confidence),
            )
            threat_id = cur.lastrowid

        await manager.broadcast({
            "event": "new_threat", "id": threat_id, "timestamp": timestamp,
            "source_ip": source_ip, "threat_type": threat_type,
            "payload": payload[:500], "severity": severity,
            "status": initial_status, "confidence": confidence,
        })

        return _block_page(403, "Threat Detected",
                           f"A <strong>{threat_type}</strong> attack was identified in your request. Access has been denied.")

    # Safe — forward to target
    if not TARGET_URL:
        return _block_page(502, "Proxy Not Configured",
                           "No target URL is set. Open the dashboard and configure a Target URL in Proxy Settings.")

    forward_url = f"{TARGET_URL}/{path}"
    skip_headers = {"host", "content-length", "transfer-encoding", "connection"}
    headers = {k: v for k, v in request.headers.items() if k.lower() not in skip_headers}

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.request(
            method=request.method,
            url=forward_url,
            headers=headers,
            content=body_bytes,
            params=dict(request.query_params),
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
