from types import ModuleType
from unittest.mock import MagicMock
import importlib
import sys


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


def test_init(monkeypatch):
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)

    messages = api.init(path="p", project_root="r", language="py", goals="g")
    assert messages == ["init"]
    assert agentapi.LATEST_MESSAGES == ["init"]
    cli_stub.init_cmd.assert_called_once_with(
        path="p",
        project_root="r",
        language="py",
        goals="g",
        bridge=bridge,
    )


def test_gather_synthesize_status(monkeypatch):
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)

    messages = api.gather(goals="g1", constraints="c1", priority="high")
    assert messages == ["g1,c1,high"]
    assert agentapi.LATEST_MESSAGES == ["g1,c1,high"]
    cli_stub.gather_cmd.assert_called_once_with(bridge=bridge)

    synth = api.synthesize(target="unit")
    assert synth == ["run:unit"]
    assert agentapi.LATEST_MESSAGES == ["run:unit"]
    cli_stub.run_pipeline_cmd.assert_called_once_with(target="unit", bridge=bridge)
    assert api.status() == ["run:unit"]
