from app.db.database import init_db, get_conn

THREATS = [
    ("2026-06-21 08:12:03", "192.168.1.45",  "SQL Injection",   "' OR '1'='1' --",                          "high",   "new"),
    ("2026-06-21 08:15:22", "10.0.0.87",     "SQL Injection",   "1; DROP TABLE users--",                    "high",   "blocked"),
    ("2026-06-21 08:31:07", "203.0.113.12",  "XSS",             "<script>document.cookie</script>",         "medium", "new"),
    ("2026-06-21 08:44:55", "198.51.100.9",  "XSS",             "<img src=x onerror=alert('xss')>",         "medium", "ignored"),
    ("2026-06-21 09:02:18", "192.168.1.101", "Path Traversal",  "../../etc/passwd",                         "high",   "blocked"),
    ("2026-06-21 09:17:34", "10.0.0.23",     "Path Traversal",  "../../../windows/system32/config/sam",     "high",   "new"),
    ("2026-06-21 09:33:49", "203.0.113.77",  "Brute Force",     "POST /login — 142 attempts in 60 seconds", "medium", "blocked"),
    ("2026-06-21 09:51:02", "198.51.100.44", "Brute Force",     "POST /admin — 38 attempts in 30 seconds",  "low",    "new"),
]

if __name__ == "__main__":
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM threats")
        conn.executemany(
            "INSERT INTO threats (timestamp, source_ip, threat_type, payload, severity, status) VALUES (?,?,?,?,?,?)",
            THREATS,
        )
    print(f"Seeded {len(THREATS)} threats.")
