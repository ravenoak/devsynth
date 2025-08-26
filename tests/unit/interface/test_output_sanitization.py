import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge


@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.fast
def test_cliuxbridge_sanitizes_script_tag_succeeds(clean_state):
    """Test that cliuxbridge sanitizes output succeeds.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("<script>alert('x')</script>Hello")
        out.assert_called_once()
        printed_text = out.call_args[0][0]
        assert getattr(printed_text, "plain", str(printed_text)) == "Hello"


@pytest.mark.medium
def test_cliuxbridge_escapes_html_succeeds(clean_state):
    """Ensure raw HTML is escaped before printing to the console.

    ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("<script>")
        out.assert_called_once()
        printed_text = out.call_args[0][0]
        assert getattr(printed_text, "plain", str(printed_text)) == "&lt;script&gt;"


@pytest.mark.medium
def test_apibridge_sanitizes_output_succeeds(clean_state):
    """Test that apibridge sanitizes output succeeds.

    ReqID: N/A"""
    bridge = APIBridge()
    bridge.display_result("<script>bad</script>Hi")
    assert bridge.messages == ["Hi"]


@pytest.mark.medium
def test_webui_sanitizes_output_succeeds(monkeypatch, clean_state):
    """Test that webui sanitizes output succeeds.

    ReqID: N/A"""
    st = ModuleType("streamlit")
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.text_input = MagicMock(return_value="t")
    st.selectbox = MagicMock(return_value="c")
    st.checkbox = MagicMock(return_value=True)
    monkeypatch.setitem(sys.modules, "streamlit", st)
    import importlib

    from devsynth.interface import webui

    # Reload the module to ensure clean state
    importlib.reload(webui)

    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("<script>bad</script>Hi")
    st.write.assert_called_once_with("Hi")


@pytest.mark.medium
def test_webapp_cmd_error_sanitized_raises_error(monkeypatch, clean_state):
    """Errors from webapp_cmd should be sanitized before printing.

    ReqID: N/A"""
    import types

    from devsynth.application.cli.cli_commands import webapp_cmd
    from devsynth.application.cli.commands import webapp_cmd as webapp_module

    bridge = CLIUXBridge()
    bridge.print = types.MethodType(lambda self, *a, **k: None, bridge)

    # Mock os.path.exists to return False
    monkeypatch.setattr(webapp_module.os.path, "exists", lambda p: False)

    # Define a function that raises an exception with HTML content
    def boom(*args, **kwargs):
        raise Exception("<script>bad</script>Danger")

    # Mock os.makedirs to raise the exception
    monkeypatch.setattr(webapp_module.os, "makedirs", boom)

    # Create a dummy progress class for testing
    class DummyProgress:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def update(self, *a, **k):
            pass

        def complete(self):
            pass

    # Override create_progress on the bridge instance
    bridge.create_progress = types.MethodType(
        lambda self, *a, **k: DummyProgress(), bridge
    )

    # Test that HTML is sanitized in error messages
    with patch("rich.console.Console.print") as out:
        webapp_cmd(framework="flask", name="app", path="/tmp", bridge=bridge)
        printed = "".join(str(c.args[0]) for c in out.call_args_list)
        assert "Danger" in printed
        assert "<script>" not in printed


@pytest.mark.medium
def test_cliuxbridge_removes_self_closing_script(clean_state):
    """Self-closing script tags should be removed entirely."""
    bridge = CLIUXBridge()
    with patch("rich.console.Console.print") as out:
        bridge.display_result("<script src='evil.js'/>Hi")
        out.assert_called_once()
        printed_text = out.call_args[0][0]
        assert getattr(printed_text, "plain", str(printed_text)) == "Hi"


@pytest.mark.medium
def test_sanitize_output_respects_env(monkeypatch):
    """Disabling sanitization should leave content untouched."""
    from devsynth.interface.ux_bridge import sanitize_output

    monkeypatch.setenv("DEVSYNTH_SANITIZATION_ENABLED", "0")
    raw = "<b>bold</b>"
    assert sanitize_output(raw) == raw
