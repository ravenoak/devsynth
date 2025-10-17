"""Steps for testing the Agent API health and metrics endpoints."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

pytest.importorskip("fastapi")

# Defer fastapi.testclient import to avoid MRO issues during collection
# Import will be done lazily when actually needed by tests
TestClient = None
from pytest_bdd import given, parsers, scenarios, then, when


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


def _module_stub(name: str, **attributes: object) -> ModuleType:
    """Return a ModuleType populated with the provided attributes."""

    module = ModuleType(name)
    for attribute, value in attributes.items():
        setattr(module, attribute, value)
    return module

scenarios(feature_path(__file__, "general", "agent_api_health_metrics.feature"))


@pytest.fixture
def api_context(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Start the Agent API with mocked settings for isolation."""

    settings_stub = MagicMock()
    settings_stub.access_token = ""
    settings_module = _module_stub(
        "devsynth.api.settings",
        settings=settings_stub,
    )
    monkeypatch.setitem(sys.modules, "devsynth.api.settings", settings_module)

    import devsynth.interface.agentapi_enhanced as agentapi

    importlib.reload(agentapi)

    client = _get_testclient()(agentapi.app)
    return {
        "client": client,
        "settings": settings_stub,
        "last_response": None,
        "auth_enabled": False,
    }


@given("the Agent API server is running")
def api_running(api_context: dict[str, object]) -> dict[str, object]:
    """Return the API context with authentication disabled."""

    settings = api_context["settings"]
    assert isinstance(settings, MagicMock)
    settings.access_token = ""
    api_context["auth_enabled"] = False
    return api_context


@given("the Agent API server is running with authentication enabled")
def api_running_with_auth(api_context: dict[str, object]) -> dict[str, object]:
    """Return the API context with authentication enabled."""

    settings = api_context["settings"]
    assert isinstance(settings, MagicMock)
    settings.access_token = "test_token"
    api_context["auth_enabled"] = True
    return api_context


@when("I GET /health")
def get_health(api_context: dict[str, object]) -> None:
    """Send a GET request to the health endpoint."""

    client = api_context["client"]
    assert isinstance(client, _get_testclient())
    api_context["last_response"] = client.get("/health")


@when("I GET /health with a valid token")
def get_health_with_valid_token(api_context: dict[str, object]) -> None:
    """Send a GET request to the health endpoint with a valid token."""

    client = api_context["client"]
    settings = api_context["settings"]
    assert isinstance(client, _get_testclient())
    assert isinstance(settings, MagicMock)
    api_context["last_response"] = client.get(
        "/health",
        headers={"Authorization": f"Bearer {settings.access_token}"},
    )


@when("I GET /health with an invalid token")
def get_health_with_invalid_token(api_context: dict[str, object]) -> None:
    """Send a GET request to the health endpoint with an invalid token."""

    client = api_context["client"]
    assert isinstance(client, _get_testclient())
    api_context["last_response"] = client.get(
        "/health", headers={"Authorization": "Bearer invalid_token"}
    )


@when("I GET /metrics")
def get_metrics(api_context: dict[str, object]) -> None:
    """Send a GET request to the metrics endpoint."""

    client = api_context["client"]
    assert isinstance(client, _get_testclient())
    api_context["last_response"] = client.get("/metrics")


@when("I GET /metrics with a valid token")
def get_metrics_with_valid_token(api_context: dict[str, object]) -> None:
    """Send a GET request to the metrics endpoint with a valid token."""

    client = api_context["client"]
    settings = api_context["settings"]
    assert isinstance(client, _get_testclient())
    assert isinstance(settings, MagicMock)
    api_context["last_response"] = client.get(
        "/metrics",
        headers={"Authorization": f"Bearer {settings.access_token}"},
    )


@when("I GET /metrics with an invalid token")
def get_metrics_with_invalid_token(api_context: dict[str, object]) -> None:
    """Send a GET request to the metrics endpoint with an invalid token."""

    client = api_context["client"]
    assert isinstance(client, _get_testclient())
    api_context["last_response"] = client.get(
        "/metrics", headers={"Authorization": "Bearer invalid_token"}
    )


@then(parsers.parse("the response status code should be {status_code:d}"))
def check_status_code(api_context: dict[str, object], status_code: int) -> None:
    """Check that the response has the expected status code."""

    response = api_context["last_response"]
    assert response is not None
    assert response.status_code == status_code


@then(parsers.parse('the response should contain "{key}" with value "{value}"'))
def check_response_key_value(
    api_context: dict[str, object], key: str, value: str
) -> None:
    """Check that the response contains the expected key-value pair."""

    response = api_context["last_response"]
    assert response is not None
    payload = response.json()
    assert key in payload
    assert payload[key] == value


@then(parsers.parse('the response should contain "{key}"'))
def check_response_contains_key(api_context: dict[str, object], key: str) -> None:
    """Check that the response contains the expected key."""

    response = api_context["last_response"]
    assert response is not None
    assert key in response.text


@then("the response should contain an error message")
def check_error_message(api_context: dict[str, object]) -> None:
    """Check that the response contains an error message."""

    response = api_context["last_response"]
    assert response is not None
    payload = response.json()
    assert "detail" in payload or "error" in payload
