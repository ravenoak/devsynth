import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, mock_open
import pytest
from pathlib import Path

@pytest.fixture
def stub_streamlit(monkeypatch):
    """Create a stub streamlit module for testing."""
    st = ModuleType("streamlit")
    
    class SS(dict):
        pass
    
    st.session_state = SS()
    st.session_state.wizard_step = 0
    st.session_state.wizard_data = {
        "title": "",
        "description": "",
        "type": "functional",
        "priority": "medium",
        "constraints": "",
    }
    
    st.write = MagicMock()
    st.progress = MagicMock()
    st.text_input = MagicMock(return_value="Test Requirement")
    st.text_area = MagicMock(return_value="Test Description")
    st.selectbox = MagicMock(return_value="functional")
    st.button = MagicMock(return_value=False)
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=MagicMock(return_value=False)),
            MagicMock(button=MagicMock(return_value=False)),
        )
    )
    
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st

def test_requirements_wizard_initial_state(stub_streamlit):
    """Test that the requirements wizard initializes with the correct state."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Reset session state to ensure clean test
    stub_streamlit.session_state.pop("wizard_step", None)
    stub_streamlit.session_state.pop("wizard_data", None)
    
    # Run the wizard
    WebUI()._requirements_wizard()
    
    # Verify initial state
    assert stub_streamlit.session_state.wizard_step == 0
    assert "title" in stub_streamlit.session_state.wizard_data
    assert "description" in stub_streamlit.session_state.wizard_data
    assert "type" in stub_streamlit.session_state.wizard_data
    assert "priority" in stub_streamlit.session_state.wizard_data
    assert "constraints" in stub_streamlit.session_state.wizard_data
    
    # Verify UI elements
    stub_streamlit.write.assert_called()
    stub_streamlit.progress.assert_called_once()

def test_requirements_wizard_step_navigation(stub_streamlit):
    """Test navigation between steps in the requirements wizard."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Set up navigation buttons
    col1_mock = MagicMock()
    col2_mock = MagicMock()
    stub_streamlit.columns.return_value = (col1_mock, col2_mock)
    
    # Test next button
    col1_mock.button.return_value = False
    col2_mock.button.return_value = True  # Next button pressed
    
    # Start at step 0
    stub_streamlit.session_state.wizard_step = 0
    WebUI()._requirements_wizard()
    
    # Should advance to step 1
    assert stub_streamlit.session_state.wizard_step == 1
    
    # Test back button
    col1_mock.button.return_value = True  # Back button pressed
    col2_mock.button.return_value = False
    
    # Start at step 1
    stub_streamlit.session_state.wizard_step = 1
    WebUI()._requirements_wizard()
    
    # Should go back to step 0
    assert stub_streamlit.session_state.wizard_step == 0

def test_requirements_wizard_save_requirements(stub_streamlit, monkeypatch):
    """Test saving requirements from the wizard."""
    import importlib
    import devsynth.interface.webui as webui
    import json
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Set up session state for the final step
    stub_streamlit.session_state.wizard_step = 4  # Last step
    stub_streamlit.session_state.wizard_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": "constraint1, constraint2",
    }
    
    # Mock the save button
    stub_streamlit.button.return_value = True  # Save button pressed
    
    # Mock open to avoid actual file operations
    m = mock_open()
    with patch("builtins.open", m):
        WebUI()._requirements_wizard()
    
    # Verify file was opened for writing
    m.assert_called_once_with("requirements_wizard.json", "w", encoding="utf-8")
    
    # Verify correct JSON was written
    handle = m()
    expected_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": ["constraint1", "constraint2"],
    }
    handle.write.assert_called_once_with(json.dumps(expected_data, indent=2))
    
    # Verify success message was displayed
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    
    with patch("builtins.open", m):
        webui_instance._requirements_wizard()
    
    webui_instance.display_result.assert_called_once()
    assert "[green]" in webui_instance.display_result.call_args[0][0]

def test_requirements_wizard_different_steps(stub_streamlit):
    """Test that different UI elements are shown at different steps."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Test step 0 (Title)
    stub_streamlit.session_state.wizard_step = 0
    WebUI()._requirements_wizard()
    stub_streamlit.text_input.assert_called()
    
    # Test step 1 (Description)
    stub_streamlit.session_state.wizard_step = 1
    WebUI()._requirements_wizard()
    stub_streamlit.text_area.assert_called()
    
    # Test step 2 (Type)
    stub_streamlit.session_state.wizard_step = 2
    WebUI()._requirements_wizard()
    stub_streamlit.selectbox.assert_called()
    
    # Test step 3 (Priority)
    stub_streamlit.session_state.wizard_step = 3
    WebUI()._requirements_wizard()
    stub_streamlit.selectbox.assert_called()
    
    # Test step 4 (Constraints)
    stub_streamlit.session_state.wizard_step = 4
    WebUI()._requirements_wizard()
    stub_streamlit.text_area.assert_called()

def test_requirements_wizard_error_handling(stub_streamlit, monkeypatch):
    """Test error handling when saving requirements."""
    import importlib
    import devsynth.interface.webui as webui
    
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Set up session state for the final step
    stub_streamlit.session_state.wizard_step = 4  # Last step
    stub_streamlit.session_state.wizard_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": "constraint1, constraint2",
    }
    
    # Mock the save button
    stub_streamlit.button.return_value = True  # Save button pressed
    
    # Create a WebUI instance with a mocked display_result method
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    
    # Mock open to raise an exception
    with patch("builtins.open", side_effect=IOError("Test error")):
        webui_instance._requirements_wizard()
    
    # Verify error message was displayed
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]