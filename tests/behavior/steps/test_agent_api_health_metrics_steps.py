"""Steps for testing the Agent API health and metrics endpoints."""

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/general/agent_api_health_metrics.feature")


@pytest.fixture
def api_context(monkeypatch):
    """Start the API with CLI commands mocked."""
    # Mock settings for authentication
    settings_stub = MagicMock()
    settings_stub.access_token = ""  # No authentication by default
    monkeypatch.setattr("devsynth.api.settings", settings_stub)

    # Import and reload the API module to apply the mocked settings
    import devsynth.interface.agentapi_enhanced as agentapi

    importlib.reload(agentapi)

    client = TestClient(agentapi.app)
    return {
        "client": client,
        "settings": settings_stub,
        "last_response": None,
        "auth_enabled": False,
    }


@given("the Agent API server is running")
def api_running(api_context):
    """Return the API context with authentication disabled."""
    api_context["settings"].access_token = ""
    api_context["auth_enabled"] = False
    return api_context


@given("the Agent API server is running with authentication enabled")
def api_running_with_auth(api_context):
    """Return the API context with authentication enabled."""
    api_context["settings"].access_token = "test_token"
    api_context["auth_enabled"] = True
    return api_context


@when("I GET /health")
def get_health(api_context):
    """Send a GET request to the health endpoint."""
    response = api_context["client"].get("/health")
    api_context["last_response"] = response


@when("I GET /health with a valid token")
def get_health_with_valid_token(api_context):
    """Send a GET request to the health endpoint with a valid token."""
    response = api_context["client"].get(
        "/health",
        headers={"Authorization": f"Bearer {api_context['settings'].access_token}"},
    )
    api_context["last_response"] = response


@when("I GET /health with an invalid token")
def get_health_with_invalid_token(api_context):
    """Send a GET request to the health endpoint with an invalid token."""
    response = api_context["client"].get(
        "/health", headers={"Authorization": "Bearer invalid_token"}
    )
    api_context["last_response"] = response


@when("I GET /metrics")
def get_metrics(api_context):
    """Send a GET request to the metrics endpoint."""
    response = api_context["client"].get("/metrics")
    api_context["last_response"] = response


@when("I GET /metrics with a valid token")
def get_metrics_with_valid_token(api_context):
    """Send a GET request to the metrics endpoint with a valid token."""
    response = api_context["client"].get(
        "/metrics",
        headers={"Authorization": f"Bearer {api_context['settings'].access_token}"},
    )
    api_context["last_response"] = response


@when("I GET /metrics with an invalid token")
def get_metrics_with_invalid_token(api_context):
    """Send a GET request to the metrics endpoint with an invalid token."""
    response = api_context["client"].get(
        "/metrics", headers={"Authorization": "Bearer invalid_token"}
    )
    api_context["last_response"] = response


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(api_context, status_code):
    """Check that the response has the expected status code."""
    assert api_context["last_response"].status_code == status_code


@then(parsers.parse('the response should contain "{key}" with value "{value}"'))
def check_response_key_value(api_context, key, value):
    """Check that the response contains the expected key-value pair."""
    response_json = api_context["last_response"].json()
    assert key in response_json
    assert response_json[key] == value


@then(parsers.parse('the response should contain "{key}"'))
def check_response_contains_key(api_context, key):
    """Check that the response contains the expected key."""
    response_text = api_context["last_response"].text
    assert key in response_text


@then("the response should contain an error message")
def check_error_message(api_context):
    """Check that the response contains an error message."""
    response_json = api_context["last_response"].json()
    assert "detail" in response_json or "error" in response_json
