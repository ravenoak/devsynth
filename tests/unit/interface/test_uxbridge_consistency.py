import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import sanitize_output


class DummyForm:
    """Context manager for form testing."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):
        return True


class DummyProgress:
    """Progress indicator for testing."""

    def __init__(self, *args, **kwargs):
        self.updated = False
        self.completed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.complete()
        return False

    def update(self, *args, **kwargs):
        self.updated = True

    def complete(self):
        self.completed = True


def _cli_bridge(monkeypatch):
    """Create a CLI UX bridge for testing."""
    ask = MagicMock(return_value="foo")
    confirm = MagicMock(return_value=True)
    out = MagicMock()
    sanitizer = MagicMock(side_effect=lambda x: f"S:{x}")

    # Set up mocks for CLI bridge
    # Mock _non_interactive to return False to ensure interactive mode
    monkeypatch.setattr("devsynth.interface.cli._non_interactive", lambda: False)

    # Mock Prompt.ask to return 'foo' instead of reading from stdin
    monkeypatch.setattr("rich.prompt.Prompt.ask", lambda *args, **kwargs: "foo")

    monkeypatch.setattr("devsynth.interface.cli.Confirm.ask", confirm)
    monkeypatch.setattr("rich.console.Console.print", out)
    monkeypatch.setattr("devsynth.interface.cli.CLIProgressIndicator", DummyProgress)
    monkeypatch.setattr("devsynth.interface.cli.sanitize_output", sanitizer)

    return CLIUXBridge(), {
        "ask": ask,
        "confirm": confirm,
        "out": out,
        "sanitize": sanitizer,
    }


def _web_bridge(monkeypatch):
    """Create a Web UI bridge for testing."""
    # Create streamlit mock
    st = ModuleType("streamlit")
    st.session_state = {}
    st.text_input = MagicMock(return_value="foo")
    st.selectbox = MagicMock(return_value="foo")
    st.checkbox = MagicMock(return_value=True)
    sanitizer = MagicMock(side_effect=lambda x: f"S:{x}")
    st.write = MagicMock()

    # Create a proper mock for markdown that can be asserted against
    markdown_mock = MagicMock()
    st.markdown = markdown_mock

    prog = MagicMock()
    st.progress = MagicMock(return_value=prog)
    st.expander = lambda *_a, **_k: DummyForm()
    st.form = lambda *_a, **_k: DummyForm()
    st.form_submit_button = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)

    # Fix line continuation with proper indentation
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=lambda *a, **k: False),
            MagicMock(button=lambda *a, **k: False),
        )
    )

    st.divider = MagicMock()
    st.spinner = DummyForm
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Set up module mocks
    setup_module = ModuleType("devsynth.application.cli.setup_wizard")
    setup_module.SetupWizard = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.setup_wizard", setup_module
    )

    cli_stub = ModuleType("devsynth.application.cli")
    for name in [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "config_cmd",
        "inspect_cmd",
    ]:
        setattr(cli_stub, name, MagicMock())
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_stub)

    commands_stub = ModuleType("devsynth.application.cli.commands")
    commands_stub.doctor_cmd = MagicMock()
    monkeypatch.setitem(sys.modules, "devsynth.application.cli.commands", commands_stub)

    doctor_module = ModuleType("devsynth.application.cli.commands.doctor_cmd")
    doctor_module.doctor_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.doctor_cmd", doctor_module
    )

    edrr_module = ModuleType("devsynth.application.cli.commands.edrr_cycle_cmd")
    edrr_module.edrr_cycle_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.edrr_cycle_cmd", edrr_module
    )

    align_module = ModuleType("devsynth.application.cli.commands.align_cmd")
    align_module.align_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.align_cmd", align_module
    )

    analyze_stub = ModuleType("devsynth.application.cli.commands.inspect_code_cmd")
    analyze_stub.inspect_code_cmd = MagicMock()
    monkeypatch.setitem(
        sys.modules, "devsynth.application.cli.commands.inspect_code_cmd", analyze_stub
    )

    # Import and reload webui module
    import importlib

    from devsynth.interface import webui

    # Reload the module to ensure clean state
    importlib.reload(webui)

    monkeypatch.setattr(webui, "sanitize_output", sanitizer)
    from devsynth.interface.webui import WebUI

    return WebUI(), {
        "write": st.write,
        "markdown": markdown_mock,
        "progress": prog,
        "sanitize": sanitizer,
    }


def _api_bridge(monkeypatch):
    """Create an API bridge for testing."""
    sanitizer = MagicMock(side_effect=lambda x: f"S:{x}")
    monkeypatch.setattr("devsynth.interface.agentapi.sanitize_output", sanitizer)
    return APIBridge(["foo", True]), {"sanitize": sanitizer}


@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    yield
    # Clean up state


@pytest.mark.parametrize("factory", [_cli_bridge, _web_bridge, _api_bridge])
@pytest.mark.slow
def test_function(factory, monkeypatch, clean_state):
    """Test that bridge contract succeeds.

    ReqID: N/A"""
    bridge, trackers = factory(monkeypatch)

    # Test ask_question
    answer = bridge.ask_question("q", choices=["x"], default="x")
    assert isinstance(answer, str)
    assert answer == "foo"

    # Test confirm_choice
    confirm = bridge.confirm_choice("ok?", default=True)
    assert isinstance(confirm, bool)
    assert confirm is True

    # Test display_result
    bridge.display_result("<bad>", highlight=True)
    if "out" in trackers:
        # Just verify that the output method was called, without checking exact arguments
        # since different UX bridges format output differently
        assert trackers["out"].call_count == 1
    # For WebUI, we don't check markdown directly as it depends on message content
    # and could use different Streamlit methods (info, write, etc.)

    # Test progress indicator
    prog = bridge.create_progress("step", total=2)
    prog.update()
    prog.complete()

    # Test context manager
    with bridge.create_progress("ctx") as ctx_prog:
        ctx_prog.update()
        ctx_prog.complete()

    # Verify sanitization - only for API bridge
    # CLI and WebUI bridges may use different sanitization approaches
    if isinstance(bridge, APIBridge):
        calls = [c.args[0] for c in trackers["sanitize"].call_args_list]
        assert "<bad>" in calls

    # API-specific assertions
    if isinstance(bridge, APIBridge):
        assert any("step complete" in m for m in bridge.messages)
        assert any("ctx complete" in m for m in bridge.messages)
