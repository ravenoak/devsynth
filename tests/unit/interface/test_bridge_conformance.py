import sys
from types import ModuleType
from unittest.mock import MagicMock
import pytest
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.agentapi import APIBridge
from devsynth.interface.ux_bridge import UXBridge, ProgressIndicator


class DummyCtx:
    """Context manager for testing."""
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _stub_streamlit(monkeypatch):
    """Create a stub for the streamlit module."""
    st = ModuleType('streamlit')
    st.session_state = {}
    st.text_input = MagicMock(return_value='')
    st.selectbox = MagicMock(return_value='')
    st.checkbox = MagicMock(return_value=True)
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.progress = MagicMock(return_value=MagicMock())
    st.expander = lambda *_a, **_k: DummyCtx()
    st.form = lambda *_a, **_k: DummyCtx()
    st.form_submit_button = MagicMock(return_value=True)
    st.button = MagicMock(return_value=False)
    
    # Fix the line continuation issue with proper indentation
    st.columns = MagicMock(return_value=(
        MagicMock(button=lambda *a, **k: False),
        MagicMock(button=lambda *a, **k: False)
    ))
    
    st.divider = MagicMock()
    st.spinner = DummyCtx
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st


def _get_webui(monkeypatch):
    """Get the WebUI class and streamlit stub."""
    st = _stub_streamlit(monkeypatch)
    import importlib
    from devsynth.interface import webui
    
    # Reload the module to ensure clean state
    importlib.reload(webui)
    
    from devsynth.interface.webui import WebUI
    return WebUI, st


def _make_cli(monkeypatch):
    """Create a CLI UX bridge instance."""
    return CLIUXBridge()


def _make_api(monkeypatch):
    """Create an API bridge instance."""
    return APIBridge([])


def _make_web(monkeypatch):
    """Create a WebUI instance."""
    WebUI, _ = _get_webui(monkeypatch)
    return WebUI()


@pytest.mark.medium
@pytest.mark.parametrize('factory', [_make_cli, _make_api, _make_web])
def test_bridge_implements_methods_succeeds(factory, monkeypatch):
    """Test that bridge implements methods succeeds.

    ReqID: N/A"""
    bridge = factory(monkeypatch)
    assert isinstance(bridge, UXBridge)
    
    for name in ['ask_question', 'confirm_choice', 'display_result', 'create_progress']:
        assert callable(getattr(bridge, name))
        
    assert isinstance(bridge.create_progress('x'), ProgressIndicator)
