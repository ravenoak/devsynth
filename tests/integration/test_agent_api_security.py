"""Integration tests for Agent API security and error handling."""

from types import ModuleType
from unittest.mock import MagicMock, patch
import importlib
import sys

import pytest
from fastapi.testclient import TestClient


def _setup_with_auth(monkeypatch, access_token="test_token"):
    """Set up the API with authentication enabled."""
    # Mock settings
    settings_stub = MagicMock()
    settings_stub.access_token = access_token
    monkeypatch.setattr("devsynth.api.settings", settings_stub)
    
    # Mock CLI modules
    cli_stub = ModuleType("devsynth.application.cli")
    
    def init_cmd(path=".", project_root=None, language=None, goals=None, *, bridge):
        bridge.display_result("init")
    
    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)
    
    # Import and reload agentapi to apply the mocks
    import devsynth.interface.agentapi as agentapi
    importlib.reload(agentapi)
    
    return {
        "client": TestClient(agentapi.app),
        "cli": cli_stub,
        "settings": settings_stub
    }


def test_api_requires_authentication(monkeypatch):
    """Test that API endpoints require authentication when access control is enabled."""
    setup = _setup_with_auth(monkeypatch)
    client = setup["client"]
    
    # Test without authentication
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Unauthorized"}
    
    # Test with invalid token
    resp = client.post(
        "/init", 
        json={"path": "proj"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Unauthorized"}
    
    # Test with valid token
    resp = client.post(
        "/init", 
        json={"path": "proj"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}


def test_api_authentication_disabled(monkeypatch):
    """Test that API endpoints don't require authentication when access control is disabled."""
    setup = _setup_with_auth(monkeypatch, access_token="")
    client = setup["client"]
    
    # Test without authentication
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}
    
    # Test with any token
    resp = client.post(
        "/init", 
        json={"path": "proj"},
        headers={"Authorization": "Bearer any_token"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}


def test_api_error_handling(monkeypatch):
    """Test that API endpoints handle errors properly."""
    setup = _setup_with_auth(monkeypatch, access_token="")
    client = setup["client"]
    cli = setup["cli"]
    
    # Mock init_cmd to raise an exception
    def init_cmd_error(*args, **kwargs):
        raise ValueError("Test error")
    
    cli.init_cmd.side_effect = init_cmd_error
    
    # Test that the API returns a 500 error when the CLI command fails
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 500
    assert "error" in resp.json()
    assert "Test error" in resp.json()["error"]


def test_api_validation(monkeypatch):
    """Test that API endpoints validate request parameters."""
    setup = _setup_with_auth(monkeypatch, access_token="")
    client = setup["client"]
    
    # Test with missing required parameter
    resp = client.post("/gather", json={})
    assert resp.status_code == 422  # Unprocessable Entity
    
    # Test with invalid parameter type
    resp = client.post("/synthesize", json={"target": 123})
    assert resp.status_code == 422  # Unprocessable Entity


def test_api_health_endpoint(monkeypatch):
    """Test the health endpoint."""
    setup = _setup_with_auth(monkeypatch)
    client = setup["client"]
    
    # Test without authentication
    resp = client.get("/health")
    assert resp.status_code == 401
    
    # Test with valid token
    resp = client.get(
        "/health",
        headers={"Authorization": "Bearer test_token"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_metrics_endpoint(monkeypatch):
    """Test the metrics endpoint."""
    setup = _setup_with_auth(monkeypatch)
    client = setup["client"]
    
    # Test without authentication
    resp = client.get("/metrics")
    assert resp.status_code == 401
    
    # Test with valid token
    resp = client.get(
        "/metrics",
        headers={"Authorization": "Bearer test_token"}
    )
    assert resp.status_code == 200
    assert "request_count" in resp.text