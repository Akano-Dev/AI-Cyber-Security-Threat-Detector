from tests.conftest import API_KEY


def test_config_requires_key(client):
    assert client.get("/api/v1/config").status_code == 401


def test_config_rejects_wrong_key(client):
    r = client.get("/api/v1/config", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_config_accepts_valid_key(client):
    r = client.get("/api/v1/config", headers={"X-API-Key": API_KEY})
    assert r.status_code == 200
    assert "rate_limit" in r.json()


def test_demo_reset_requires_key(client):
    assert client.post("/api/v1/demo/reset").status_code == 401
    assert client.post("/api/v1/demo/reset", headers={"X-API-Key": API_KEY}).status_code == 200
