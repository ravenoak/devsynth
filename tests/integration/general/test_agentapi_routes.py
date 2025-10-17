import pytest

pytest.importorskip("fastapi")

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

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
def test_init_route_succeeds(monkeypatch):
    """Test that init route succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    client = _get_testclient()(agentapi.app)
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}
    cli_stub.init_cmd.assert_called_once()


@pytest.mark.medium
def test_gather_route_succeeds(monkeypatch):
    """Test that gather route succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    client = _get_testclient()(agentapi.app)
    resp = client.post(
        "/gather", json={"goals": "g1", "constraints": "c1", "priority": "high"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["g1,c1,high"]}
    cli_stub.gather_cmd.assert_called_once()


@pytest.mark.medium
def test_synthesize_and_status_succeeds(monkeypatch):
    """Test that synthesize and status succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    client = _get_testclient()(agentapi.app)
    resp = client.post("/synthesize", json={"target": "unit"})
    assert resp.json() == {"messages": ["run:unit"]}
    status = client.get("/status")
    assert status.json() == {"messages": ["run:unit"]}
    cli_stub.run_pipeline_cmd.assert_called_once()
