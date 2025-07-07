import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def mock_init_cmd(monkeypatch):
    """Fixture to mock init_cmd for testing."""
    init_cmd = MagicMock()
    
    # Create a module for cli
    cli_module = ModuleType("devsynth.application.cli")
    cli_module.init_cmd = init_cmd
    
    # Add the module to sys.modules
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)
    
    return init_cmd


def test_onboarding_page(mock_streamlit, mock_init_cmd):
    """Test the onboarding_page method."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Call the onboarding_page method
    bridge.onboarding_page()
    
    # Verify that the header was called with the correct text
    mock_streamlit.header.assert_called_with("Project Initialization")
    
    # Verify that the form was created
    assert mock_streamlit.form.called
    
    # Simulate form submission
    mock_streamlit.form_submit_button.return_value = True
    
    # Call the onboarding_page method again
    bridge.onboarding_page()
    
    # Verify that init_cmd was called
    assert mock_init_cmd.called


def test_onboarding_page_no_submit(mock_streamlit, mock_init_cmd):
    """Test the onboarding_page method when the form is not submitted."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Simulate form not being submitted
    mock_streamlit.form_submit_button.return_value = False
    
    # Call the onboarding_page method
    bridge.onboarding_page()
    
    # Verify that init_cmd was not called
    assert not mock_init_cmd.called