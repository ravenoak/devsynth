import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call
import pytest
from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()
    monkeypatch.setitem(sys.modules, 'streamlit', st)
    return st


@pytest.fixture
def mock_init_cmd(monkeypatch):
    """Fixture to mock init_cmd for testing."""
    init_cmd = MagicMock()
    cli_module = ModuleType('devsynth.application.cli')
    cli_module.init_cmd = init_cmd
    monkeypatch.setitem(sys.modules, 'devsynth.application.cli', cli_module)
    return init_cmd


def test_onboarding_page_succeeds(mock_streamlit, mock_init_cmd):
    """Test the onboarding_page method.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    bridge = WebUI()
    bridge.onboarding_page()
    mock_streamlit.header.assert_called_with('Project Initialization')
    assert mock_streamlit.form.called
    mock_streamlit.form_submit_button.return_value = True
    bridge.onboarding_page()
    assert mock_init_cmd.called


def test_onboarding_page_no_submit_succeeds(mock_streamlit, mock_init_cmd):
    """Test the onboarding_page method when the form is not submitted.

ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    bridge = WebUI()
    mock_streamlit.form_submit_button.return_value = False
    bridge.onboarding_page()
    assert not mock_init_cmd.called
