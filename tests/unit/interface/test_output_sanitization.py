import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
from devsynth.interface.agentapi import APIBridge
from devsynth.interface.cli import CLIUXBridge


def test_cliuxbridge_sanitizes_output_succeeds():
    """Test that cliuxbridge sanitizes output succeeds.

ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch('rich.console.Console.print') as out:
        bridge.display_result("<script>alert('x')</script>Hello")
        out.assert_called_once_with('Hello', highlight=False)


def test_cliuxbridge_escapes_html_succeeds():
    """Ensure raw HTML is escaped before printing to the console.

ReqID: N/A"""
    bridge = CLIUXBridge()
    with patch('rich.console.Console.print') as out:
        bridge.display_result('<script>')
        out.assert_called_once_with('&lt;script&gt;', highlight=False)


def test_apibridge_sanitizes_output_succeeds():
    """Test that apibridge sanitizes output succeeds.

ReqID: N/A"""
    bridge = APIBridge()
    bridge.display_result('<script>bad</script>Hi')
    assert bridge.messages == ['Hi']


def test_webui_sanitizes_output_succeeds(monkeypatch):
    """Test that webui sanitizes output succeeds.

ReqID: N/A"""
    st = ModuleType('streamlit')
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.text_input = MagicMock(return_value='t')
    st.selectbox = MagicMock(return_value='c')
    st.checkbox = MagicMock(return_value=True)
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    bridge = WebUI()
    bridge.display_result('<script>bad</script>Hi')
    st.write.assert_called_once_with('Hi')


def test_webapp_cmd_error_sanitized_raises_error(monkeypatch):
    """Errors from webapp_cmd should be sanitized before printing.

ReqID: N/A"""
    from devsynth.application.cli.cli_commands import webapp_cmd
    import types
    bridge = CLIUXBridge()
    bridge.print = types.MethodType(lambda self, *a, **k: None, bridge)
    monkeypatch.setattr('devsynth.interface.ux_bridge.sanitize_output', lambda
        x: str(x))
    monkeypatch.setattr('devsynth.application.cli.cli_commands.os.path.exists',
        lambda p: False)

    def boom(*args, **kwargs):
        raise Exception('<script>bad</script>Danger')
    monkeypatch.setattr('devsynth.application.cli.cli_commands.os.makedirs',
        boom)


    class DummyProgress:

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def update(self, *a, **k):
            pass

        def complete(self):
            pass
    monkeypatch.setattr(
        'devsynth.application.cli.cli_commands.bridge.create_progress', lambda
        *a, **k: DummyProgress())
    with patch('rich.console.Console.print') as out:
        webapp_cmd(framework='flask', name='app', path='/tmp', bridge=bridge)
        printed = ''.join(str(c.args[0]) for c in out.call_args_list)
        assert 'Danger' in printed
        assert '<script>' not in printed
