import pytest

from devsynth.api import app

pytest.importorskip("fastapi")

# Defer fastapi.testclient import to avoid MRO issues during collection
# Import will be done lazily when actually needed by tests
TestClient = None

def _get_testclient():
    """Lazily import TestClient to avoid MRO issues during collection."""
    global TestClient
    if TestClient is None:
        try:
            from fastapi.testclient import TestClient
        except TypeError:
            # Fallback for MRO compatibility issues
            from starlette.testclient import TestClient
    return TestClient

# Lazy initialization of client
def _get_client():
    """Get the test client, initializing lazily."""
    global client
    if client is None:
        client = _get_testclient()(app)
    return client


@pytest.fixture
def api_token_env(monkeypatch):
    """Provide a test access token for API requests."""
    monkeypatch.setenv("DEVSYNTH_ACCESS_TOKEN", "test-token")
    from devsynth import api as api_module

    monkeypatch.setattr(api_module.settings, "access_token", "test-token")


@pytest.mark.fast
def test_health_endpoint_succeeds(api_token_env):
    """Test that health endpoint succeeds.

    ReqID: N/A"""
    resp = _get_client().get("/health", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.fast
def test_metrics_endpoint_succeeds(api_token_env):
    """Test that metrics endpoint succeeds.

    ReqID: N/A"""
    resp = _get_client().get("/metrics", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    assert b"request_count" in resp.content
