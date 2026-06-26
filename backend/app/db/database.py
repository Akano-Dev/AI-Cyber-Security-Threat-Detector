"""SQLite connection + schema. (Phase 5 swaps this for SQLAlchemy + Postgres.)"""
import sqlite3

from app.config import settings


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    return conn


def healthcheck() -> bool:
    """Return True if a trivial query succeeds. Closes its own connection."""
    try:
        conn = get_conn()
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
        return True
    except Exception:
        return False


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threats (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                source_ip   TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                payload     TEXT NOT NULL,
                severity    TEXT NOT NULL CHECK(severity IN ('low','medium','high')),
                status      TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','blocked','ignored')),
                confidence  REAL
            )
        """)
        try:
            conn.execute("ALTER TABLE threats ADD COLUMN confidence REAL")
        except Exception:
            pass  # column already exists

        conn.execute("""
            CREATE TABLE IF NOT EXISTS blocked_ips (
                ip         TEXT PRIMARY KEY,
                blocked_at TEXT NOT NULL
            )
        """)
