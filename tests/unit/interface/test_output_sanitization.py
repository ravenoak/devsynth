from types import ModuleType
from unittest.mock import MagicMock, patch
import sys

from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.agentapi import APIBridge


def test_cliuxbridge_sanitizes_output():
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("<script>alert('x')</script>Hello")
        out.assert_called_once_with("Hello", highlight=False)


def test_apibridge_sanitizes_output():
    bridge = APIBridge()
    bridge.display_result("<script>bad</script>Hi")
    assert bridge.messages == ["Hi"]


def test_webui_sanitizes_output(monkeypatch):
    st = ModuleType("streamlit")
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.text_input = MagicMock(return_value="t")
    st.selectbox = MagicMock(return_value="c")
    st.checkbox = MagicMock(return_value=True)
    monkeypatch.setitem(sys.modules, "streamlit", st)

    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("<script>bad</script>Hi")
    st.write.assert_called_once_with("Hi")
