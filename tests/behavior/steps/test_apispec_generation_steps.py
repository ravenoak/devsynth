"""BDD steps for the ``apispec`` command."""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then

import importlib


@pytest.fixture
def apispec_context(monkeypatch):
    """Provide a patched ``apispec_cmd`` for testing."""
    import devsynth.application.cli.apispec as api_module

    mock_cmd = MagicMock()
    monkeypatch.setattr(api_module, "apispec_cmd", mock_cmd)
    importlib.reload(api_module)
    return {"cmd": mock_cmd}


scenarios("../features/general/apispec_generation.feature")


@pytest.mark.medium
@given("the apispec_generation feature context")
def given_context(apispec_context):
    """Return the patched context."""
    return apispec_context


@pytest.mark.medium
@when("we execute the apispec_generation workflow")
def when_execute(apispec_context):
    """Invoke the ``apispec`` command."""
    from devsynth.application.cli.apispec import apispec_cmd

    apispec_cmd()
    apispec_context["cmd"] = apispec_cmd


@pytest.mark.medium
@then("the apispec_generation workflow completes")
def then_complete(apispec_context):
    """Ensure the command was called."""
    apispec_context["cmd"].assert_called_once()
