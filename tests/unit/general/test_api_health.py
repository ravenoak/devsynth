import pytest

from devsynth.api import app

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def api_token_env(monkeypatch):
    """Provide a test access token for API requests."""
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "test-token")
    from devsynth import api as api_module

    monkeypatch.setattr(api_module.settings, "access_token", "test-token")


def test_health_endpoint_succeeds(api_token_env):
    """Test that health endpoint succeeds.

    ReqID: N/A"""
    resp = client.get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_metrics_endpoint_succeeds(api_token_env):
    """Test that metrics endpoint succeeds.

    ReqID: N/A"""
    resp = client.get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert b"request_count" in resp.content
