"""Steps exercising the Agent API endpoints."""

from types import ModuleType
from unittest.mock import MagicMock
import importlib
import sys

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, when, then, scenarios

scenarios("../features/agent_api_interactions.feature")


@pytest.fixture
def api_context(monkeypatch):
    """Start the API with CLI commands mocked."""

    cli_stub = ModuleType("devsynth.application.cli")

    def init_cmd(path=".", project_root=None, language=None, goals=None, *, bridge):
        bridge.display_result("init")

    def gather_cmd(output_file="requirements_plan.yaml", *, bridge):
        g = bridge.ask_question("g")
        c = bridge.ask_question("c")
        p = bridge.ask_question("p")
        bridge.display_result(f"{g},{c},{p}")

    def run_pipeline_cmd(target=None, *, bridge):
        bridge.display_result(f"run:{target}")

    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    cli_stub.gather_cmd = MagicMock(side_effect=gather_cmd)
    cli_stub.run_pipeline_cmd = MagicMock(side_effect=run_pipeline_cmd)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)
    client = TestClient(agentapi.app)
    return {"client": client, "cli": cli_stub}


@given("the Agent API server is running")
def api_running(api_context):
    """Return the API context."""
    return api_context


@when("I POST to /init")
def post_init(api_context):
    api_context["client"].post("/init", json={"path": "proj"})


@when("I POST to /gather")
def post_gather(api_context):
    api_context["client"].post(
        "/gather",
        json={"goals": "g1", "constraints": "c1", "priority": "high"},
    )


@when("I POST to /synthesize")
def post_synthesize(api_context):
    api_context["client"].post("/synthesize", json={"target": "unit"})


@when("I GET /status")
def get_status(api_context):
    api_context["status"] = api_context["client"].get("/status")


@then("the CLI init command should be called")
def cli_init_called(api_context):
    assert api_context["cli"].init_cmd.called


@then("the CLI gather command should be called")
def cli_gather_called(api_context):
    assert api_context["cli"].gather_cmd.called


@then("the CLI run_pipeline command should be called")
def cli_run_pipeline_called(api_context):
    assert api_context["cli"].run_pipeline_cmd.called


@then('the status message should be "run:unit"')
def status_run_unit(api_context):
    assert api_context["status"].json() == {"messages": ["run:unit"]}
