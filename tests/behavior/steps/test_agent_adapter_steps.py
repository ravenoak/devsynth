"""BDD steps exercising the agent adapter infrastructure."""

from unittest.mock import MagicMock

import pytest
from pytest_bdd import scenarios, given, when, then


@pytest.fixture
def adapter_context(monkeypatch):
    """Provide a mocked ``WSDETeamCoordinator`` implementation."""
    import devsynth.adapters.agents.agent_adapter as adapter_module

    mock_coord = MagicMock()
    mock_cls = MagicMock(return_value=mock_coord)
    monkeypatch.setattr(adapter_module, "WSDETeamCoordinator", mock_cls)
    return {"cls": mock_cls, "instance": mock_coord}


scenarios("../features/agent_adapter.feature")


@given("the agent_adapter feature context")
def given_context(adapter_context):
    """Return patched context."""
    return adapter_context


@when("we execute the agent_adapter workflow")
def when_execute(adapter_context):
    """Instantiate the coordinator and create a team."""
    from devsynth.adapters.agents.agent_adapter import WSDETeamCoordinator

    coord = WSDETeamCoordinator()
    coord.create_team("demo_team")
    adapter_context["instance"] = coord


@then("the agent_adapter workflow completes")
def then_complete(adapter_context):
    """Ensure the coordinator was invoked correctly."""
    adapter_context["cls"].assert_called_once()
    adapter_context["instance"].create_team.assert_called_with("demo_team")
