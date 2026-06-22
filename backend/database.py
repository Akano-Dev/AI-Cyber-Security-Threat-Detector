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
