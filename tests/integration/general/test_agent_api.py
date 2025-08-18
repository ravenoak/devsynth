import pytest

pytest.importorskip("fastapi")

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

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

    def spec_cmd(requirements_file="requirements.md", *, bridge):
        bridge.display_result(f"spec:{requirements_file}")

    @pytest.mark.medium
    def test_cmd(spec_file="specs.md", output_dir=None, *, bridge):
        """Test that cmd succeeds.

        ReqID: N/A"""
        bridge.display_result(f"test:{spec_file}")

    def code_cmd(output_dir=None, *, bridge):
        bridge.display_result("code")

    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    cli_stub.gather_cmd = MagicMock(side_effect=gather_cmd)
    cli_stub.run_pipeline_cmd = MagicMock(side_effect=run_pipeline_cmd)
    cli_stub.spec_cmd = MagicMock(side_effect=spec_cmd)
    cli_stub.test_cmd = MagicMock(side_effect=test_cmd)
    cli_stub.code_cmd = MagicMock(side_effect=code_cmd)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)
    doctor_stub = ModuleType("devsynth.application.cli.commands.doctor_cmd")

    def doctor_cmd(path=".", fix=False, *, bridge):
        bridge.display_result(f"doctor:{path}:{fix}")

    doctor_stub.doctor_cmd = MagicMock(side_effect=doctor_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_stub
    )
    edrr_stub = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")

    def edrr_cycle_cmd(prompt, context=None, max_iterations=3, *, bridge):
        bridge.display_result(f"edrr:{prompt}")

    edrr_stub.edrr_cycle_cmd = MagicMock(side_effect=edrr_cycle_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_stub
    )
    import devsynth.interface.agentapi as agentapi

    importlib.reload(agentapi)
    return {
        "cli": cli_stub,
        "agentapi": agentapi,
        "doctor_cmd": doctor_stub.doctor_cmd,
        "edrr_cycle_cmd": edrr_stub.edrr_cycle_cmd,
    }


@pytest.mark.medium
def test_init_route_succeeds(monkeypatch):
    """Test that init route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post("/init", json={"path": "proj"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["init"]}
    setup["cli"].init_cmd.assert_called_once()


@pytest.mark.medium
def test_gather_route_succeeds(monkeypatch):
    """Test that gather route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post(
        "/gather", json={"goals": "g1", "constraints": "c1", "priority": "high"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["g1,c1,high"]}
    setup["cli"].gather_cmd.assert_called_once()


@pytest.mark.medium
def test_synthesize_and_status_succeeds(monkeypatch):
    """Test that synthesize and status.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post("/synthesize", json={"target": "unit"})
    assert resp.json() == {"messages": ["run:unit"]}
    status = client.get("/status")
    assert status.json() == {"messages": ["run:unit"]}
    setup["cli"].run_pipeline_cmd.assert_called_once()


@pytest.mark.medium
def test_spec_route_succeeds(monkeypatch):
    """Test that spec route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post("/spec", json={"requirements_file": "custom_reqs.md"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["spec:custom_reqs.md"]}
    setup["cli"].spec_cmd.assert_called_once()
    args, kwargs = setup["cli"].spec_cmd.call_args
    assert kwargs["requirements_file"] == "custom_reqs.md"


@pytest.mark.medium
def test_test_route_succeeds(monkeypatch):
    """Test that test route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post(
        "/test", json={"spec_file": "custom_specs.md", "output_dir": "tests"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["test:custom_specs.md"]}
    setup["cli"].test_cmd.assert_called_once()


@pytest.mark.medium
def test_code_route_succeeds(monkeypatch):
    """Test that code route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post("/code", json={"output_dir": "src"})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["code"]}
    setup["cli"].code_cmd.assert_called_once()


@pytest.mark.medium
def test_doctor_route_succeeds(monkeypatch):
    """Test that doctor route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post("/doctor", json={"path": "project", "fix": True})
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["doctor:project:True"]}
    setup["doctor_cmd"].assert_called_once()


@pytest.mark.medium
def test_edrr_cycle_route_succeeds(monkeypatch):
    """Test that edrr cycle route.

    ReqID: N/A"""
    setup = _setup(monkeypatch)
    client = TestClient(setup["agentapi"].app)
    resp = client.post(
        "/edrr-cycle", json={"prompt": "Improve code", "max_iterations": 5}
    )
    assert resp.status_code == 200
    assert resp.json() == {"messages": ["edrr:Improve code"]}
    setup["edrr_cycle_cmd"].assert_called_once()
