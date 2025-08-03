import sys
from types import ModuleType
from unittest.mock import MagicMock
import pytest
from devsynth.interface.simple_run import run_workflow
from devsynth.interface.ux_bridge import UXBridge


class DummyBridge(UXBridge):

    def __init__(self) ->None:
        self.messages: list[str] = []

    def ask_question(self, message: str, *, choices=None, default=None,
        show_default=True):
        return 'init'

    def confirm_choice(self, message: str, *, default: bool=False) ->bool:
        return True

    def display_result(self, message: str, *, highlight: bool=False) ->None:
        self.messages.append(message)


@pytest.mark.medium
def test_run_workflow_cli_succeeds(monkeypatch):
    """Test that run workflow cli succeeds.

ReqID: N/A"""
    bridge = DummyBridge()
    called = {}

    def fake_execute(cmd, args):
        called['cmd'] = cmd
        return {'summary': 'ok'}
    monkeypatch.setattr('devsynth.interface.simple_run.execute_command',
        fake_execute)
    result = run_workflow(bridge)
    assert called['cmd'] == 'init'
    assert result == {'summary': 'ok'}
    assert 'ok' in bridge.messages


@pytest.mark.medium
def test_run_workflow_webui_succeeds(monkeypatch):
    """Test that run workflow webui succeeds.

ReqID: N/A"""
    st = ModuleType('streamlit')
    st.selectbox = MagicMock(return_value='init')
    st.text_input = MagicMock(return_value='init')
    st.checkbox = MagicMock(return_value=True)
    st.progress = MagicMock()
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.sidebar = ModuleType('sidebar')
    st.sidebar.radio = MagicMock(return_value='Onboarding')
    st.sidebar.title = MagicMock()
    st.expander = lambda *a, **k: DummyBridge()
    st.form = lambda *a, **k: DummyBridge()
    st.form_submit_button = MagicMock(return_value=True)
    st.set_page_config = MagicMock()
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    from devsynth.interface.webui import WebUI
    bridge = WebUI()
    monkeypatch.setattr(bridge, 'ask_question', lambda *a, **k: 'init')
    monkeypatch.setattr(bridge, 'confirm_choice', lambda *a, **k: True)
    messages = []
    monkeypatch.setattr(bridge, 'display_result', lambda msg, **k: messages
        .append(msg))

    def fake_execute(cmd, args):
        return {'summary': 'ok'}
    monkeypatch.setattr('devsynth.interface.simple_run.execute_command',
        fake_execute)
    result = run_workflow(bridge)
    assert result == {'summary': 'ok'}
    assert 'ok' in messages
