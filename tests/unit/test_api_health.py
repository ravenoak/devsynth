import os
from devsynth.api import app
from fastapi.testclient import TestClient

os.environ["DEVSYNTH_ACCESS_TOKEN"] = "test-token"
client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint():
    resp = client.get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert b"request_count" in resp.content
