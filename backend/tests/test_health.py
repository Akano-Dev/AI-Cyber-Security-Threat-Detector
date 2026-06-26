def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_stats_shape(client):
    r = client.get("/api/v1/stats")
    assert r.status_code == 200
    body = r.json()
    for key in ("total", "blocked_ips", "by_type", "by_severity", "by_status"):
        assert key in body
