import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast

scenarios(feature_path(__file__, "general", "agent_api_stub.feature"))


@pytest.fixture
def api_context(monkeypatch):
    cli_stub = ModuleType("devsynth.application.cli")
    cli_stub.init_cmd = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)
    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)
    ctx = {"api": agentapi, "cli": cli_stub}
    return ctx


@given("the Agent API stub is available")
def api_available(api_context):
    return api_context


@when("I call the init endpoint")
def call_init(api_context):
    req = api_context["api"].InitRequest(path=".")
    api_context["api"].init_endpoint(req, token=None)


@then("the init command should be executed through the bridge")
def check_called(api_context):
    assert api_context["cli"].init_cmd.called
