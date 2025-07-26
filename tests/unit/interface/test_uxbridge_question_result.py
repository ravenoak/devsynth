"""Tests for UXBridge.ask_question and display_result parity.

This covers the roadmap requirement in `pre_1.0_release_plan.md` lines
29-35 that all interfaces share consistent UXBridge behavior.
"""

import importlib
import sys
from unittest.mock import MagicMock

import pytest

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.agentapi import APIBridge

from .test_streamlit_mocks import make_streamlit_mock


def _cli_bridge(monkeypatch):
    monkeypatch.setattr("rich.prompt.Prompt.ask", MagicMock(return_value="foo"))
    monkeypatch.setattr("devsynth.interface.cli.validate_safe_input", lambda x: x)
    monkeypatch.setattr("devsynth.interface.cli.sanitize_output", lambda x: f"S:{x}")
    monkeypatch.setattr(
        "devsynth.interface.shared_bridge.SharedBridgeMixin._format_for_output",
        lambda self, message, *, highlight=False, message_type=None: f"S:{message}",
    )
    out = MagicMock()
    monkeypatch.setattr("rich.console.Console.print", out)
    return CLIUXBridge(), out


def _web_bridge(monkeypatch):
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setattr("devsynth.interface.webui_bridge.sanitize_output", lambda x: f"S:{x}")
    monkeypatch.setattr(
        "devsynth.interface.shared_bridge.SharedBridgeMixin._format_for_output",
        lambda self, message, *, highlight=False, message_type=None: f"S:{message}",
    )
    import devsynth.interface.webui_bridge as webui_bridge
    importlib.reload(webui_bridge)
    from devsynth.interface.webui_bridge import WebUIBridge
    return WebUIBridge(), st


def _api_bridge(monkeypatch):
    monkeypatch.setattr("devsynth.interface.agentapi.sanitize_output", lambda x: f"S:{x}")
    return APIBridge(["foo"]) , None


@pytest.mark.parametrize("factory", [_cli_bridge, _web_bridge, _api_bridge])
def test_ask_question_and_display_result_consistency(factory, monkeypatch):
    """All bridges should return the same answers and sanitized results."""
    bridge, tracker = factory(monkeypatch)
    answer = bridge.ask_question("Q?", choices=["foo"], default="foo")
    assert answer == "foo"
    bridge.display_result("<bad>")
    if isinstance(bridge, APIBridge):
        assert bridge.messages[-1] == "S:<bad>"
    elif isinstance(bridge, CLIUXBridge):
        tracker.assert_called_once_with("S:<bad>", style=None)
    else:
        assert bridge.messages[-1] == "S:<bad>"

