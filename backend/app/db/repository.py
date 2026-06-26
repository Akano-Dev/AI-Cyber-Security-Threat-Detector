"""Data-access helpers. Endpoints talk to the DB only through this module."""
from app.db.database import get_conn

_COLUMNS = "timestamp, source_ip, threat_type, payload, severity, status, confidence"


def insert_threat(timestamp, source_ip, threat_type, payload, severity, status, confidence) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO threats ({_COLUMNS}) VALUES (?,?,?,?,?,?,?)",
            (timestamp, source_ip, threat_type, payload, severity, status, confidence),
        )
        return cur.lastrowid


def list_threats() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM threats ORDER BY timestamp DESC").fetchall()
    return [dict(r) for r in rows]


def count_threats() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM threats").fetchone()[0]


def get_threat(threat_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM threats WHERE id = ?", (threat_id,)).fetchone()
    return dict(row) if row else None


def set_status(threat_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE threats SET status = ? WHERE id = ?", (status, threat_id))


def clear_all() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM threats")
        conn.execute("DELETE FROM blocked_ips")


# ── blocked IPs ──────────────────────────────────────────────────────────────

def load_blocked_ips() -> set[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT ip FROM blocked_ips").fetchall()
    return {r["ip"] for r in rows}


def persist_block(ip: str, timestamp: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO blocked_ips (ip, blocked_at) VALUES (?, ?)",
            (ip, timestamp),
        )


def remove_block(ip: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM blocked_ips WHERE ip = ?", (ip,))
