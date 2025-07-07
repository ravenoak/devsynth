import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, call

import pytest

from tests.unit.interface.test_webui_enhanced import _mock_streamlit


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()
    
    # Add session_state for requirements wizard
    st.session_state = {}
    st.session_state["wizard_step"] = 0
    st.session_state["wizard_data"] = {}
    
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def mock_spec_cmd(monkeypatch):
    """Fixture to mock spec_cmd for testing."""
    spec_cmd = MagicMock()
    
    # Create a module for cli
    cli_module = ModuleType("devsynth.application.cli")
    cli_module.spec_cmd = spec_cmd
    
    # Add the module to sys.modules
    monkeypatch.setitem(sys.modules, "devsynth.application.cli", cli_module)
    
    return spec_cmd


@pytest.fixture
def mock_requirement_types(monkeypatch):
    """Fixture to mock RequirementType and RequirementPriority enums."""
    # Create a module for requirement
    req_module = ModuleType("devsynth.domain.models.requirement")
    
    # Create mock enums
    class MockRequirementType:
        FUNCTIONAL = "functional"
        NON_FUNCTIONAL = "non_functional"
        CONSTRAINT = "constraint"
        
    class MockRequirementPriority:
        MUST_HAVE = "must_have"
        SHOULD_HAVE = "should_have"
        COULD_HAVE = "could_have"
        WONT_HAVE = "wont_have"
    
    req_module.RequirementType = MockRequirementType
    req_module.RequirementPriority = MockRequirementPriority
    
    # Add the module to sys.modules
    monkeypatch.setitem(sys.modules, "devsynth.domain.models.requirement", req_module)


def test_requirements_page(mock_streamlit, mock_spec_cmd, mock_requirement_types):
    """Test the requirements_page method."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Call the requirements_page method
    bridge.requirements_page()
    
    # Verify that the header was called with the correct text
    mock_streamlit.header.assert_called_with("Requirements Gathering")
    
    # Verify that the form was created
    assert mock_streamlit.form.called
    
    # Simulate form submission
    mock_streamlit.form_submit_button.return_value = True
    
    # Call the requirements_page method again
    bridge.requirements_page()
    
    # Verify that spec_cmd was called
    assert mock_spec_cmd.called


def test_requirements_wizard(mock_streamlit, mock_requirement_types):
    """Test the _requirements_wizard method."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance
    bridge = WebUI()
    
    # Call the _requirements_wizard method
    bridge._requirements_wizard()
    
    # Verify that the form was created
    assert mock_streamlit.form.called
    
    # Verify that the session state was updated
    assert "wizard_step" in mock_streamlit.session_state
    assert "wizard_data" in mock_streamlit.session_state
    
    # Simulate form submission and advance to next step
    mock_streamlit.form_submit_button.return_value = True
    mock_streamlit.session_state["wizard_step"] = 0
    
    # Call the _requirements_wizard method again
    bridge._requirements_wizard()
    
    # Verify that the wizard step was incremented
    assert mock_streamlit.session_state["wizard_step"] == 1
    
    # Simulate completion of all steps
    mock_streamlit.session_state["wizard_step"] = 3
    
    # Call the _requirements_wizard method again
    result = bridge._requirements_wizard()
    
    # Verify that the wizard returned the collected data
    assert result is not None
    assert isinstance(result, dict)