import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from rich.panel import Panel

from devsynth.interface.cli import CLIUXBridge


@pytest.mark.fast
def test_cli_bridge_methods_succeeds():
    """Test that cli bridge methods succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.prompt.Prompt.ask", return_value="ans") as ask:
        resp = bridge.ask_question("Q?")
        ask.assert_called_once()
        assert resp == "ans"
    with patch("rich.prompt.Confirm.ask", return_value=True) as conf:
        assert bridge.confirm_choice("ok?") is True
        conf.assert_called_once()
    with patch("rich.console.Console.print") as pr:
        bridge.display_result("done", highlight=True)
        assert pr.call_count == 1
        printed_obj = pr.call_args[0][0]
        assert isinstance(printed_obj, Panel)
        assert printed_obj.renderable == "done"
        assert pr.call_args.kwargs.get("style") == "highlight"


@pytest.mark.fast
def test_webui_bridge_methods_succeeds(monkeypatch):
    """Test that webui bridge methods succeeds.

    ReqID: N/A"""
    st = ModuleType("streamlit")
    st.text_input = MagicMock(return_value="text")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.write = MagicMock()
    st.markdown = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    assert bridge.ask_question("msg") == "text"
    st.text_input.assert_called_once()
    assert bridge.confirm_choice("y?") is True
    st.checkbox.assert_called_once()
    bridge.display_result("hi", highlight=False)
    st.write.assert_called_once_with("hi")
