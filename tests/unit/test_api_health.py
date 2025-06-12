from devsynth.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_metrics_endpoint():
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert b"request_count" in resp.content
