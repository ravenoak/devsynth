"""Ensure UXBridge parity across CLI and WebUI.

This test verifies the requirement outlined in Phase 1 of the
pre-1.0 release roadmap (lines 40-45) that both interfaces use the
same UXBridge abstraction for prompts and results.
"""

import importlib
import sys
from unittest.mock import MagicMock

import pytest

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import sanitize_output
from tests.fixtures.streamlit_mocks import make_streamlit_mock


def _setup_cli(monkeypatch):
    """Set up CLI environment for testing."""
    # Store original functions to restore later
    original_sanitize = getattr(
        sys.modules["devsynth.interface.cli"], "sanitize_output", None
    )

    # Set up mocks
    monkeypatch.setattr("devsynth.interface.cli.sanitize_output", lambda x: x)
    cli_out = MagicMock()
    monkeypatch.setattr("rich.console.Console.print", cli_out)

    # Mock _non_interactive to return False to ensure interactive mode
    monkeypatch.setattr("devsynth.interface.cli._non_interactive", lambda: False)

    # Mock Prompt.ask to return a default value instead of reading from stdin
    monkeypatch.setattr(
        "rich.prompt.Prompt.ask", lambda *args, **kwargs: kwargs.get("default", "foo")
    )

    # Mock Confirm.ask to return True
    monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)

    return CLIUXBridge(), cli_out


def _setup_webui(monkeypatch):
    """Set up WebUI environment for testing."""
    # Create streamlit mock
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Set up sanitize_output mock
    monkeypatch.setattr("devsynth.interface.webui_bridge.sanitize_output", lambda x: x)

    # Import and reload the module to ensure clean state
    import devsynth.interface.webui_bridge as webui_bridge

    importlib.reload(webui_bridge)
    from devsynth.interface.webui_bridge import WebUIBridge

    return WebUIBridge(), st


@pytest.mark.medium
@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    # Store original modules and functions to restore later
    original_sanitize_module = getattr(sanitize_output, "__module__", None)
    original_sanitize_func = getattr(
        sys.modules.get(original_sanitize_module, {}), "sanitize_output", None
    )

    # Clear any WebUIBridge messages that might exist
    if "devsynth.interface.webui_bridge" in sys.modules:
        bridge_module = sys.modules["devsynth.interface.webui_bridge"]
        if hasattr(bridge_module, "WebUIBridge"):
            WebUIBridge = bridge_module.WebUIBridge
            if hasattr(WebUIBridge, "messages") and isinstance(
                WebUIBridge.messages, list
            ):
                WebUIBridge.messages.clear()

    yield

    # Clean up state after test
    # Reload modules to ensure clean state for next test
    if "devsynth.interface.webui_bridge" in sys.modules:
        importlib.reload(sys.modules["devsynth.interface.webui_bridge"])

    if "devsynth.interface.cli" in sys.modules:
        importlib.reload(sys.modules["devsynth.interface.cli"])


def test_prompt_and_result_consistency(monkeypatch, clean_state):
    """CLI and WebUI should return identical answers and formatted output."""
    # Store original sanitize_output function
    original_sanitize = getattr(
        sys.modules.get(sanitize_output.__module__, {}), "sanitize_output", None
    )

    try:
        # Set up sanitize_output mock
        monkeypatch.setattr(
            sanitize_output.__module__ + ".sanitize_output", lambda x: x
        )

        # Set up CLI and WebUI bridges
        cli_bridge, cli_out = _setup_cli(monkeypatch)
        web_bridge, _st = _setup_webui(monkeypatch)

        # Test question functionality
        cli_answer = cli_bridge.ask_question("Question?", default="foo")
        web_answer = web_bridge.ask_question("Question?", default="foo")
        assert cli_answer == web_answer == "foo"

        # Test result display functionality
        cli_bridge.display_result("Result")
        web_bridge.display_result("Result")

        printed_cli = cli_out.call_args[0][0]
        assert printed_cli == web_bridge.messages[-1]
    finally:
        # Clean up any remaining mocks
        if original_sanitize is not None:
            setattr(
                sys.modules[sanitize_output.__module__],
                "sanitize_output",
                original_sanitize,
            )
