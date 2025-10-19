"""Integration tests for Agent API security and error handling."""

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

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


def _setup_with_auth(monkeypatch, access_token="test_token"):
    """Set up the API with authentication enabled."""
    settings_stub = MagicMock()
    settings_stub.access_token = access_token
    monkeypatch.setattr("devsynth.api.settings", settings_stub)
    cli_stub = ModuleType("devsynth.application.cli")

    def init_cmd(path=".", project_root=None, language=None, goals=None, *, bridge):
        bridge.display_result("init")

    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)
    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)
    return {
        "client": _get_testclient()(agentapi.app),
        "cli": cli_stub,
        "settings": settings_stub,
    }


@pytest.mark.medium
def test_api_requires_authentication_succeeds(monkeypatch):
    """Test that API endpoints require authentication when access control is enabled.

    ReqID: N/A"""
    setup = _setup_with_auth(monkeypatch)
    client = setup["client"]
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Unauthorized"}
    resp = client.post(
        "/init",
        json={"path": "proj"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Unauthorized"}
    resp = client.post(
        "/init", json={"path": "proj"}, headers={"Authorization": "Bearer test_token"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}


@pytest.mark.medium
def test_api_authentication_disabled_succeeds(monkeypatch):
    """Test that API endpoints don't require authentication when access control is disabled.

    ReqID: N/A"""
    setup = _setup_with_auth(monkeypatch, access_token="")
    client = setup["client"]
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}
    resp = client.post(
        "/init", json={"path": "proj"}, headers={"Authorization": "Bearer any_token"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}


@pytest.mark.medium
def test_api_error_handling_raises_error(monkeypatch):
    """Test that API endpoints handle errors properly.

    ReqID: N/A"""
    setup = _setup_with_auth(monkeypatch, access_token="")
    client = setup["client"]
    cli = setup["cli"]

    def init_cmd_error(*args, **kwargs):
        raise ValueError("Test error")

    cli.init_cmd.side_effect = init_cmd_error
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 500
    assert "error" in resp.json()
    assert "Test error" in resp.json()["error"]


@pytest.mark.medium
def test_api_validation_is_valid(monkeypatch):
    """Test that API endpoints validate request parameters.

    ReqID: N/A"""
    setup = _setup_with_auth(monkeypatch, access_token="")
    client = setup["client"]
    resp = client.post("/gather", json={})
    assert resp.status_code == 422
    resp = client.post("/synthesize", json={"target": 123})
    assert resp.status_code == 422


@pytest.mark.medium
def test_api_health_endpoint_succeeds(monkeypatch):
    """Test the health endpoint.

    ReqID: N/A"""
    setup = _setup_with_auth(monkeypatch)
    client = setup["client"]
    resp = client.get("/health")
    assert resp.status_code == 401
    resp = client.get("/health", headers={"Authorization": "Bearer test_token"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.medium
def test_api_metrics_endpoint_succeeds(monkeypatch):
    """Test the metrics endpoint.

    ReqID: N/A"""
    setup = _setup_with_auth(monkeypatch)
    client = setup["client"]
    resp = client.get("/metrics")
    assert resp.status_code == 401
    resp = client.get("/metrics", headers={"Authorization": "Bearer test_token"})
    assert resp.status_code == 200
    assert "request_count" in resp.text
