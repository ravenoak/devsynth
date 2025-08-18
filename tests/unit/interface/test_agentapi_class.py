import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from devsynth.interface import agentapi


def _setup(monkeypatch):
    """Set up the test environment with mocked CLI modules."""
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
    def test_cmd_succeeds(spec_file="specs.md", output_dir=None, *, bridge):
        bridge.display_result(f"test:{spec_file}:{output_dir}")

    def code_cmd(output_dir=None, *, bridge):
        bridge.display_result(f"code:{output_dir}")

    def doctor_cmd(path=".", fix=False, *, bridge):
        bridge.display_result(f"doctor:{path}:{fix}")

    def edrr_cycle_cmd(prompt, context=None, max_iterations=3, *, bridge):
        bridge.display_result(f"edrr:{prompt}:{context}:{max_iterations}")

    cli_stub.init_cmd = MagicMock(side_effect=init_cmd)
    cli_stub.gather_cmd = MagicMock(side_effect=gather_cmd)
    cli_stub.run_pipeline_cmd = MagicMock(side_effect=run_pipeline_cmd)
    cli_stub.spec_cmd = MagicMock(side_effect=spec_cmd)
    cli_stub.test_cmd = MagicMock(side_effect=test_cmd_succeeds)
    cli_stub.code_cmd = MagicMock(side_effect=code_cmd)
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    doctor_module = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_module.doctor_cmd = MagicMock(side_effect=doctor_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_module
    )

    edrr_module = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_module.edrr_cycle_cmd = MagicMock(side_effect=edrr_cycle_cmd)
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_module
    )

    from devsynth.interface import webui

    # Reload the modules to ensure clean state
    importlib.reload(webui)
    importlib.reload(agentapi)

    return cli_stub, agentapi


@pytest.fixture
def clean_state():
    """Set up and tear down a clean state for tests."""
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.slow
def test_init_succeeds(monkeypatch, clean_state):
    """Test that init succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    messages = api.init(path="p", project_root="r", language="py", goals="g")
    assert messages == ["init"]
    assert agentapi.LATEST_MESSAGES == ["init"]
    cli_stub.init_cmd.assert_called_once_with(
        path="p", project_root="r", language="py", goals="g", bridge=bridge
    )


@pytest.mark.slow
def test_gather_synthesize_status_succeeds(monkeypatch, clean_state):
    """Test that gather synthesize status.

    ReqID: N/A"""
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


@pytest.mark.slow
def test_spec_succeeds(monkeypatch, clean_state):
    """Test that spec succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    messages = api.spec(requirements_file="custom_reqs.md")
    assert messages == ["spec:custom_reqs.md"]
    assert agentapi.LATEST_MESSAGES == ["spec:custom_reqs.md"]
    cli_stub.spec_cmd.assert_called_once_with(
        requirements_file="custom_reqs.md", bridge=bridge
    )


@pytest.mark.slow
def test_test_succeeds(monkeypatch, clean_state):
    """Test that test succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    messages = api.test(spec_file="custom_specs.md", output_dir="tests/output")
    assert messages == ["test:custom_specs.md:tests/output"]
    assert agentapi.LATEST_MESSAGES == ["test:custom_specs.md:tests/output"]
    cli_stub.test_cmd.assert_called_once_with(
        spec_file="custom_specs.md", output_dir="tests/output", bridge=bridge
    )


@pytest.mark.slow
def test_code_succeeds(monkeypatch, clean_state):
    """Test that code succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    messages = api.code(output_dir="src/output")
    assert messages == ["code:src/output"]
    assert agentapi.LATEST_MESSAGES == ["code:src/output"]
    cli_stub.code_cmd.assert_called_once_with(output_dir="src/output", bridge=bridge)


@pytest.mark.slow
def test_doctor_succeeds(monkeypatch, clean_state):
    """Test that doctor succeeds.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    doctor_module = sys.modules["devsynth.application.cli.commands.doctor_cmd"]
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    messages = api.doctor(path="custom_path", fix=True)
    assert messages == ["doctor:custom_path:True"]
    assert agentapi.LATEST_MESSAGES == ["doctor:custom_path:True"]
    doctor_module.doctor_cmd.assert_called_once_with(
        path="custom_path", fix=True, bridge=bridge
    )


@pytest.mark.slow
def test_edrr_cycle_succeeds(monkeypatch, clean_state):
    """Test that edrr cycle.

    ReqID: N/A"""
    cli_stub, agentapi = _setup(monkeypatch)
    edrr_module = sys.modules["devsynth.application.cli.commands.edrr_cycle_cmd"]
    bridge = agentapi.APIBridge()
    api = agentapi.AgentAPI(bridge)
    messages = api.edrr_cycle(
        prompt="test prompt", context="test context", max_iterations=5
    )
    assert messages == ["edrr:test prompt:test context:5"]
    assert agentapi.LATEST_MESSAGES == ["edrr:test prompt:test context:5"]
    edrr_module.edrr_cycle_cmd.assert_called_once_with(
        prompt="test prompt", context="test context", max_iterations=5, bridge=bridge
    )
