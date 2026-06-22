import asyncio
import json
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import init_db, get_conn
from detection import analyze
import ml_model

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory blocklist ---
blocklist: set[str] = set()

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


# --- App lifecycle ---

@app.on_event("startup")
def startup():
    init_db()
    loaded = ml_model.load_model()
    print("ML model loaded." if loaded else "WARNING: model.pkl not found — run python train.py first.")


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
        blocklist.add(row["source_ip"])

    return await _set_status(threat_id, "blocked")


@app.post("/threats/{threat_id}/ignore")
async def ignore_threat(threat_id: int):
    return await _set_status(threat_id, "ignored")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(ws)
