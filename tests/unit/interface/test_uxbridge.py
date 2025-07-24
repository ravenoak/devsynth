"""Ensure UXBridge parity across CLI and WebUI.

This test verifies the requirement outlined in Phase 1 of the
pre-1.0 release roadmap (lines 40-45) that both interfaces use the
same UXBridge abstraction for prompts and results.
"""

import importlib
import sys
from unittest.mock import MagicMock

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.ux_bridge import sanitize_output

from .test_streamlit_mocks import make_streamlit_mock


def _setup_cli(monkeypatch):
    monkeypatch.setattr("rich.prompt.Prompt.ask", MagicMock(return_value="foo"))
    monkeypatch.setattr("devsynth.interface.cli.validate_safe_input", lambda x: x)
    monkeypatch.setattr("devsynth.interface.cli.sanitize_output", lambda x: x)
    cli_out = MagicMock()
    monkeypatch.setattr("rich.console.Console.print", cli_out)
    return CLIUXBridge(), cli_out


def _setup_webui(monkeypatch):
    st = make_streamlit_mock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setattr("devsynth.interface.webui_bridge.sanitize_output", lambda x: x)
    import devsynth.interface.webui_bridge as webui_bridge

    importlib.reload(webui_bridge)
    from devsynth.interface.webui_bridge import WebUIBridge

    return WebUIBridge(), st


def test_prompt_and_result_consistency(monkeypatch):
    """CLI and WebUI should return identical answers and formatted output."""

    monkeypatch.setattr(sanitize_output.__module__ + ".sanitize_output", lambda x: x)

    cli_bridge, cli_out = _setup_cli(monkeypatch)
    web_bridge, _st = _setup_webui(monkeypatch)

    cli_answer = cli_bridge.ask_question("Question?")
    web_answer = web_bridge.ask_question("Question?", default="foo")
    assert cli_answer == web_answer == "foo"

    cli_bridge.display_result("Result")
    web_bridge.display_result("Result")

    printed_cli = cli_out.call_args[0][0]
    assert printed_cli == web_bridge.messages[-1]
