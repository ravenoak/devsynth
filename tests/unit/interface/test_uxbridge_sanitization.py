import sys
import pytest
from types import ModuleType
from unittest.mock import MagicMock, patch
from devsynth.interface.cli import CLIUXBridge
from devsynth.interface.agentapi import APIBridge

def _mock_streamlit(monkeypatch):
    st = ModuleType('streamlit')
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.text_input = MagicMock(return_value='t')
    st.selectbox = MagicMock(return_value='c')
    st.checkbox = MagicMock(return_value=True)
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st

@pytest.mark.medium

@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state

def test_with_clean_state(clean_state):
    """Test that cliuxbridge sanitizes display result succeeds.

    ReqID: N/A"""

    bridge = CLIUXBridge()
    with patch('rich.console.Console.print') as out:
        bridge.display_result('<script>')
        out.assert_called_once_with('&lt;script&gt;', highlight=False)

@pytest.mark.medium
def test_apibridge_sanitizes_display_result_succeeds():
    """Test that apibridge sanitizes display result succeeds.

    ReqID: N/A"""
    bridge = APIBridge()
    bridge.display_result('<script>')
    assert bridge.messages == ['&lt;script&gt;']

@pytest.mark.medium
def test_webui_sanitizes_display_result_succeeds(monkeypatch):
    """Test that webui sanitizes display result succeeds.

    ReqID: N/A"""
    st = _mock_streamlit(monkeypatch)
    import importlib
    
    import importlib
    from devsynth.interface import webui
    # Reload the module to ensure clean state
    importlib.reload(module)

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    bridge = WebUI()
    bridge.display_result('<script>')
    st.write.assert_called_once_with('&lt;script&gt;')