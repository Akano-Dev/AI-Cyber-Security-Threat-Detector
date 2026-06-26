def test_analyze_safe(client):
    r = client.post("/api/v1/analyze", json={
        "source_ip": "10.1.1.1", "payload": "GET /index.html", "user_agent": "Mozilla/5.0",
    })
    assert r.status_code == 200
    assert r.json()["verdict"] == "safe"


def test_analyze_sql_injection(client):
    r = client.post("/api/v1/analyze", json={
        "source_ip": "10.1.1.2", "payload": "' OR '1'='1' --", "user_agent": "Mozilla/5.0",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "threat"
    assert body["threat_type"] == "SQL Injection"
    assert body["severity"] == "high"


def test_analyze_suspicious_user_agent(client):
    r = client.post("/api/v1/analyze", json={
        "source_ip": "10.1.1.3", "payload": "GET /admin", "user_agent": "sqlmap/1.7",
    })
    assert r.json()["threat_type"] == "Suspicious User-Agent"
