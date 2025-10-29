import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

fastapi = pytest.importorskip("fastapi")
if fastapi:
    from fastapi.testclient import TestClient


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
def test_json_requests_succeeds(monkeypatch):
    """Test that json requests succeeds.

    ReqID: AGENTAPI-001"""

    if not fastapi:
        pytest.skip("FastAPI not available")

    # TestClient is imported above if fastapi is available

    cli_stub, agentapi = _setup(monkeypatch)
    client = TestClient(agentapi.app)
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"], "metadata": None}
    resp = client.post(
        "/gather", json={"goals": "g1", "constraints": "c1", "priority": "high"}
    )
    assert resp.json() == {"messages": ["g1,c1,high"], "metadata": None}
    resp = client.post("/synthesize", json={"target": "unit"})
    assert resp.json() == {"messages": ["run:SynthesisTarget.UNIT"], "metadata": None}
    status = client.get("/status")
    assert status.json() == {"messages": ["run:SynthesisTarget.UNIT"], "metadata": None}
    assert cli_stub.init_cmd.called
    assert cli_stub.gather_cmd.called
    assert cli_stub.run_pipeline_cmd.called
