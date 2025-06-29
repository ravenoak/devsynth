import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge


class DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _stub_streamlit(monkeypatch):
    st = ModuleType("streamlit")
    st.text_input = MagicMock(return_value="text")
    st.selectbox = MagicMock(return_value="choice")
    st.checkbox = MagicMock(return_value=True)
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.progress = MagicMock(return_value=MagicMock(progress=MagicMock()))
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


def test_bridge_methods(monkeypatch):
    # CLI bridge
    bridge = CLIUXBridge()
    with patch("rich.prompt.Prompt.ask", return_value="ans"):
        assert bridge.ask_question("q") == "ans"
    with patch("rich.prompt.Confirm.ask", return_value=True):
        assert bridge.confirm_choice("ok") is True
    with patch("rich.console.Console.print"):
        bridge.display_result("done")
    prog = bridge.create_progress("step")
    prog.update()
    prog.complete()

    # API bridge
    api_bridge = APIBridge(["foo", True])
    assert api_bridge.ask_question("q") == "foo"
    assert api_bridge.confirm_choice("ok") is True
    api_bridge.display_result("msg")
    api_prog = api_bridge.create_progress("step")
    api_prog.update()
    api_prog.complete()

    # WebUI bridge
    _stub_streamlit(monkeypatch)
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    web_bridge = WebUI()
    assert web_bridge.ask_question("q") in ("text", "choice")
    assert web_bridge.confirm_choice("c") is True
    web_bridge.display_result("res", highlight=True)
    web_prog = web_bridge.create_progress("x")
    web_prog.update()
    web_prog.complete()
