"""Integration tests for the :class:`AgentAPI` wrapper."""

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


def _setup(monkeypatch):
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
    return cli_stub, agentapi


@pytest.mark.medium
def test_init_succeeds(monkeypatch):
    """Test that init succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    msgs = api.init(path="proj")
    assert msgs == ["init"]
    cli_stub.init_cmd.assert_called_once()


@pytest.mark.medium
def test_gather_succeeds(monkeypatch):
    """Test that gather succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    msgs = api.gather(goals="g1", constraints="c1", priority="high")
    assert msgs == ["g1,c1,high"]
    cli_stub.gather_cmd.assert_called_once()


@pytest.mark.medium
def test_synthesize_and_status_succeeds(monkeypatch):
    """Test that synthesize and status.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    msgs = api.synthesize(target="unit")
    assert msgs == ["run:unit"]
    assert api.status() == ["run:unit"]
    cli_stub.run_pipeline_cmd.assert_called_once()
