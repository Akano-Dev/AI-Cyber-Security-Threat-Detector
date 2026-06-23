import sqlite3

DB_PATH = "threats.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
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


def load_blocked_ips() -> set[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT ip FROM blocked_ips").fetchall()
    return {row["ip"] for row in rows}


def persist_block(ip: str, timestamp: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO blocked_ips (ip, blocked_at) VALUES (?, ?)",
            (ip, timestamp),
        )


def remove_block(ip: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM blocked_ips WHERE ip = ?", (ip,))
