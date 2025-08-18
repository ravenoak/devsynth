"""Tests for UXBridge.ask_question and display_result parity.

This covers the roadmap requirement in `pre_1.0_release_plan.md` lines
29-35 that all interfaces share consistent UXBridge behavior.
"""

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, call

import pytest

from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge
from tests.fixtures.streamlit_mocks import make_streamlit_mock


@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    yield
    # Clean up state


def _cli_bridge(monkeypatch):
    """Create a CLI UX bridge for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Tuple of (bridge, tracker) where tracker is the mocked console.print
    """
    # Set up sanitization
    monkeypatch.setattr("devsynth.interface.cli.sanitize_output", lambda x: f"S:{x}")

    # Ensure non-interactive mode for prompts
    monkeypatch.setenv("DEVSYNTH_NONINTERACTIVE", "1")

    # Simplify formatting
    monkeypatch.setattr(
        "devsynth.interface.shared_bridge.SharedBridgeMixin._format_for_output",
        lambda self, message, *, highlight=False, message_type=None: f"S:{message}",
    )

    # Set up console output mock
    out = MagicMock()
    monkeypatch.setattr("rich.console.Console.print", out)

    return CLIUXBridge(), out


def _web_bridge(monkeypatch):
    """Create a Web UI bridge for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Tuple of (bridge, tracker) where tracker is the streamlit mock
    """
    # Create streamlit mock
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    # Set up sanitization
    monkeypatch.setattr(
        "devsynth.interface.webui_bridge.sanitize_output", lambda x: f"S:{x}"
    )

    # Set up output formatting
    monkeypatch.setattr(
        "devsynth.interface.shared_bridge.SharedBridgeMixin._format_for_output",
        lambda self, message, *, highlight=False, message_type=None: f"S:{message}",
    )

    # Import and reload webui_bridge module
    import devsynth.interface.webui_bridge as webui_bridge

    importlib.reload(webui_bridge)
    from devsynth.interface.webui_bridge import WebUIBridge

    return WebUIBridge(), st


def _dpg_bridge(monkeypatch):
    """Create a Dear PyGUI bridge for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Tuple of (bridge, tracker) where tracker captures dpg.add_text calls
    """
    dpg_pkg = ModuleType("dearpygui")
    dpg_mod = ModuleType("dearpygui.dearpygui")

    dpg_mod.is_viewport_created = MagicMock(return_value=True)

    class _Window:
        def __enter__(self):
            return "win"

        def __exit__(self, exc_type, exc, tb):
            return False

    dpg_mod.window = MagicMock(return_value=_Window())
    dpg_mod.add_selectable = MagicMock()
    dpg_mod.add_button = MagicMock()
    dpg_mod.add_text = MagicMock()
    dpg_mod.delete_item = MagicMock()

    dpg_pkg.dearpygui = dpg_mod
    monkeypatch.setitem(sys.modules, "dearpygui", dpg_pkg)
    monkeypatch.setitem(sys.modules, "dearpygui.dearpygui", dpg_mod)

    # Set up output formatting before loading bridge
    monkeypatch.setattr(
        "devsynth.interface.shared_bridge.SharedBridgeMixin._format_for_output",
        lambda self, message, *, highlight=False, message_type=None: f"S:{message}",
    )

    import devsynth.interface.dpg_bridge as dpg_bridge

    importlib.reload(dpg_bridge)

    # Set up sanitization and event loop stub
    monkeypatch.setattr(dpg_bridge, "sanitize_output", lambda x: f"S:{x}")
    monkeypatch.setattr(
        dpg_bridge.DearPyGUIBridge,
        "_event_loop",
        staticmethod(lambda condition: None),
    )

    return dpg_bridge.DearPyGUIBridge(), dpg_mod


def _api_bridge(monkeypatch):
    """Create an API bridge for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Tuple of (bridge, None) as API bridge doesn't need a tracker
    """
    monkeypatch.setattr(
        "devsynth.interface.agentapi.sanitize_output", lambda x: f"S:{x}"
    )
    return APIBridge(["foo"]), None


@pytest.mark.parametrize(
    "factory", [_cli_bridge, _web_bridge, _api_bridge, _dpg_bridge]
)
@pytest.mark.medium
def test_ask_question_and_display_result_consistency(factory, monkeypatch, clean_state):
    """All bridges should return the same answers and sanitized results."""
    bridge, tracker = factory(monkeypatch)

    # Test ask_question
    answer = bridge.ask_question("Q?", choices=["foo"], default="foo")
    assert answer == "foo"

    # Test display_result
    bridge.display_result("<bad>")

    # Verify results based on bridge type
    if isinstance(bridge, APIBridge):
        assert bridge.messages[-1] == "S:<bad>"
    elif isinstance(bridge, CLIUXBridge):
        tracker.assert_called_once_with("S:<bad>", style=None)
    elif bridge.__class__.__name__ == "DearPyGUIBridge":
        tracker.add_text.assert_any_call("S:<bad>")
    else:
        assert bridge.messages[-1] == "S:<bad>"
