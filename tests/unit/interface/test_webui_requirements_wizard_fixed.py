import sys
from types import ModuleType
from unittest.mock import MagicMock, patch, mock_open, call
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
            MagicMock(button=MagicMock(return_value=False))
        )
    )
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def clean_state():
    """Set up and tear down a clean state for tests."""
    # Set up clean state
    yield
    # Clean up state


@pytest.mark.medium
def test_requirements_wizard_initialization(stub_streamlit, clean_state):
    """Test that the requirements wizard initializes with the correct state.

    ReqID: N/A"""
    import importlib
    from devsynth.interface import webui
    # Reload the module to ensure clean state
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.pop("wizard_step", None)
    stub_streamlit.session_state.pop("wizard_data", None)
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0
    assert "title" in stub_streamlit.session_state.wizard_data
    assert "description" in stub_streamlit.session_state.wizard_data
    assert "type" in stub_streamlit.session_state.wizard_data
    assert "priority" in stub_streamlit.session_state.wizard_data
    assert "constraints" in stub_streamlit.session_state.wizard_data
    stub_streamlit.write.assert_called()
    stub_streamlit.progress.assert_called_once()


@pytest.mark.medium
def test_requirements_wizard_step_navigation_succeeds(stub_streamlit, clean_state):
    """Test navigation between steps in the requirements wizard.

    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    col1_mock = MagicMock()
    col2_mock = MagicMock()
    stub_streamlit.columns.return_value = col1_mock, col2_mock
    col1_mock.button.return_value = False
    col2_mock.button.return_value = True
    stub_streamlit.session_state.wizard_step = 0
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 1
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False
    stub_streamlit.session_state.wizard_step = 1
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0


@pytest.mark.medium
def test_requirements_wizard_state_persistence_succeeds(stub_streamlit, clean_state):
    """Test that wizard state is preserved when navigating between steps.
    
    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    from devsynth.interface.webui_bridge import WebUIBridge

    # Set up input mocks
    stub_streamlit.text_input.return_value = "Test Title"
    stub_streamlit.text_area.return_value = "Test Description"
    stub_streamlit.selectbox.return_value = "functional"
    
    # Initialize wizard data
    stub_streamlit.session_state.wizard_step = 0
    stub_streamlit.session_state.wizard_data = {}
    
    # Step 1: Title
    WebUI()._requirements_wizard()
    assert "title" in stub_streamlit.session_state.wizard_data
    assert stub_streamlit.session_state.wizard_data["title"] == "Test Title"
    
    # Directly set the wizard step to 1 (simulating navigation to step 2)
    stub_streamlit.session_state.wizard_step = 1
    
    # Step 2: Description
    WebUI()._requirements_wizard()
    assert "description" in stub_streamlit.session_state.wizard_data
    assert stub_streamlit.session_state.wizard_data["description"] == "Test Description"
    
    # Directly set the wizard step back to 0 (simulating navigation back to step 1)
    stub_streamlit.session_state.wizard_step = 0
    
    # Run the wizard again at step 1
    WebUI()._requirements_wizard()
    
    # Verify data is still preserved
    assert "title" in stub_streamlit.session_state.wizard_data
    assert stub_streamlit.session_state.wizard_data["title"] == "Test Title"
    assert "description" in stub_streamlit.session_state.wizard_data
    assert stub_streamlit.session_state.wizard_data["description"] == "Test Description"


@pytest.mark.medium
def test_requirements_wizard_complete_navigation_succeeds(stub_streamlit, clean_state):
    """Test navigation through all steps of the wizard.
    
    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    # Set up navigation mocks
    col1_mock = MagicMock()
    col2_mock = MagicMock()
    stub_streamlit.columns.return_value = col1_mock, col2_mock
    col1_mock.button.return_value = False
    col2_mock.button.return_value = True
    
    # Set up input mocks
    stub_streamlit.text_input.return_value = "Test Title"
    stub_streamlit.text_area.return_value = "Test Description"
    stub_streamlit.selectbox.return_value = "functional"
    
    # Initialize wizard
    stub_streamlit.session_state.wizard_step = 0
    stub_streamlit.session_state.wizard_data = {}
    
    # Navigate through all steps
    for step in range(4):  # 0 to 3, then to 4
        WebUI()._requirements_wizard()
        assert stub_streamlit.session_state.wizard_step == step + 1
        
    # At the last step
    assert stub_streamlit.session_state.wizard_step == 4
    
    # Try to go beyond the last step (should stay at the last step)
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 4
    
    # Navigate back through all steps
    col1_mock.button.return_value = True
    col2_mock.button.return_value = False
    
    for step in range(4, 0, -1):  # 4 to 1, then to 0
        WebUI()._requirements_wizard()
        assert stub_streamlit.session_state.wizard_step == step - 1
        
    # At the first step
    assert stub_streamlit.session_state.wizard_step == 0
    
    # Try to go before the first step (should stay at the first step)
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0


@pytest.mark.medium
def test_requirements_wizard_preserves_existing_state(stub_streamlit, clean_state):
    """Wizard should not reset state if values already exist."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 3
    stub_streamlit.session_state.wizard_data = {
        "title": "Existing",
        "description": "desc",
        "type": "functional",
        "priority": "medium",
        "constraints": "",
    }
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 3
    assert stub_streamlit.session_state.wizard_data["title"] == "Existing"


@pytest.mark.medium
def test_requirements_wizard_save_requirements_succeeds(stub_streamlit, monkeypatch, clean_state):
    """Test saving requirements from the wizard.

    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    import json

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 4
    stub_streamlit.session_state.wizard_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": "constraint1, constraint2",
    }
    stub_streamlit.button.return_value = True
    m = mock_open()
    with patch("builtins.open", m):
        result = WebUI()._requirements_wizard()
    m.assert_called_once_with("requirements_wizard.json", "w", encoding="utf-8")
    handle = m()
    expected_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": ["constraint1", "constraint2"],
    }
    handle.write.assert_called_once_with(json.dumps(expected_data, indent=2))
    assert result == expected_data
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    stub_streamlit.session_state.wizard_step = 4
    stub_streamlit.session_state.wizard_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": "constraint1, constraint2",
    }
    with patch("builtins.open", m):
        result = webui_instance._requirements_wizard()
    webui_instance.display_result.assert_called_once()
    assert "[green]" in webui_instance.display_result.call_args[0][0]
    assert result == expected_data


@pytest.mark.medium
def test_requirements_wizard_different_steps_succeeds(stub_streamlit, clean_state):
    """Test that different UI elements are shown at different steps.

    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 0
    WebUI()._requirements_wizard()
    stub_streamlit.text_input.assert_called()
    stub_streamlit.session_state.wizard_step = 1
    WebUI()._requirements_wizard()
    stub_streamlit.text_area.assert_called()
    stub_streamlit.session_state.wizard_step = 2
    WebUI()._requirements_wizard()
    stub_streamlit.selectbox.assert_called()
    stub_streamlit.session_state.wizard_step = 3
    WebUI()._requirements_wizard()
    stub_streamlit.selectbox.assert_called()
    stub_streamlit.session_state.wizard_step = 4
    WebUI()._requirements_wizard()
    stub_streamlit.text_area.assert_called()


@pytest.mark.medium
def test_requirements_wizard_string_step_succeeds(stub_streamlit, clean_state):
    """Wizard should handle string step values."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = "2"
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 2


@pytest.mark.medium
def test_requirements_wizard_float_step_succeeds(stub_streamlit, clean_state):
    """Wizard should handle float step values."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 2.7
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 2


@pytest.mark.medium
def test_requirements_wizard_negative_step_succeeds(stub_streamlit, clean_state):
    """Wizard should handle negative step values and clamp to 0."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = -5
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0


@pytest.mark.medium
def test_requirements_wizard_too_large_step_succeeds(stub_streamlit, clean_state):
    """Wizard should handle step values larger than the total steps and clamp to max."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 100
    WebUI()._requirements_wizard()
    # The wizard has 5 steps (0-4), so this should be clamped to 4
    assert stub_streamlit.session_state.wizard_step == 4


@pytest.mark.medium
def test_requirements_wizard_none_step_succeeds(stub_streamlit, clean_state):
    """Wizard should handle None step values and default to 0."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = None
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0


@pytest.mark.medium
def test_requirements_wizard_invalid_step_succeeds(stub_streamlit, clean_state):
    """Wizard should handle invalid step values and default to 0."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = "invalid"
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0


@pytest.mark.medium
def test_requirements_wizard_error_handling_raises_error(stub_streamlit, monkeypatch, clean_state):
    """Test error handling when saving requirements.

    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 4
    stub_streamlit.session_state.wizard_data = {
        "title": "Test Requirement",
        "description": "Test Description",
        "type": "functional",
        "priority": "medium",
        "constraints": "constraint1, constraint2",
    }
    stub_streamlit.button.return_value = True
    webui_instance = WebUI()
    webui_instance.display_result = MagicMock()
    with patch("builtins.open", side_effect=IOError("Test error")):
        webui_instance._requirements_wizard()
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]


@pytest.mark.medium
def test_requirements_wizard_navigation_error_handling_succeeds(stub_streamlit, monkeypatch, clean_state):
    """Test that the wizard handles errors during navigation gracefully.
    
    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    # Reload the module to ensure we have the latest version
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Set up navigation mocks to raise an exception
    col1_mock = MagicMock()
    col2_mock = MagicMock()
    stub_streamlit.columns.return_value = (col1_mock, col2_mock)
    
    # Make the button raise an exception when called
    col2_mock.button.side_effect = Exception("Navigation error")
    
    # Initialize wizard
    stub_streamlit.session_state.wizard_step = 0
    stub_streamlit.session_state.wizard_data = {}
    
    # Create a WebUI instance with a mock display_result method
    webui_instance = WebUI()
    original_display_result = webui_instance.display_result
    webui_instance.display_result = MagicMock()
    
    # Run the wizard, which should handle the navigation error
    webui_instance._requirements_wizard()
    
    # Verify that the error was handled and displayed
    webui_instance.display_result.assert_called_once()
    assert "ERROR" in webui_instance.display_result.call_args[0][0]
    assert "navigation" in webui_instance.display_result.call_args[0][0].lower()
    
    # Verify that the wizard step didn't change
    assert stub_streamlit.session_state.wizard_step == 0
    
    # Restore the original display_result method
    webui_instance.display_result = original_display_result


@pytest.mark.medium
def test_requirements_wizard_session_state_error_handling_succeeds(stub_streamlit, monkeypatch, clean_state):
    """Test that the wizard handles errors when accessing session state.
    
    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui
    from unittest.mock import patch

    # Reload the module to ensure we have the latest version
    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    
    # Create a WebUI instance with a mock display_result method
    webui_instance = WebUI()
    original_display_result = webui_instance.display_result
    webui_instance.display_result = MagicMock()
    
    # Patch the get_session_value function to raise an exception
    with patch.object(webui.WebUIBridge, 'get_session_value', 
                     side_effect=AttributeError("Simulated session state error")):
        # Run the wizard, which should handle the session state error
        webui_instance._requirements_wizard()
    
    # Verify that the error was handled
    assert webui_instance.display_result.call_count > 0, "display_result was not called"
    
    # Check that at least one call has the expected error message
    error_calls = [call for call in webui_instance.display_result.call_args_list 
                  if "ERROR" in call[0][0] and "Simulated session state error" in call[0][0]]
    assert len(error_calls) > 0, "No calls with the expected error message"
    
    # Restore the original display_result method
    webui_instance.display_result = original_display_result


@pytest.mark.medium
def test_requirements_wizard_step_normalization_error_handling_succeeds(stub_streamlit, monkeypatch, clean_state):
    """Test that the wizard handles errors during step normalization.
    
    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI
    from devsynth.interface.webui_bridge import WebUIBridge
    
    # Mock the normalize_wizard_step method to raise an exception
    original_normalize = WebUIBridge.normalize_wizard_step
    WebUIBridge.normalize_wizard_step = MagicMock(side_effect=Exception("Normalization error"))
    
    try:
        # Initialize wizard with a problematic step value
        stub_streamlit.session_state.wizard_step = "problematic"
        
        # Create a WebUI instance with a mock display_result method
        webui_instance = WebUI()
        webui_instance.display_result = MagicMock()
        
        # Run the wizard, which should handle the normalization error
        webui_instance._requirements_wizard()
        
        # Verify that the error was handled
        webui_instance.display_result.assert_called()
        assert "ERROR" in webui_instance.display_result.call_args[0][0]
    finally:
        # Restore the original method
        WebUIBridge.normalize_wizard_step = original_normalize


@pytest.mark.medium
def test_requirements_wizard_resets_after_save(stub_streamlit, monkeypatch, clean_state):
    """Wizard should reset state after saving."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = 4
    stub_streamlit.session_state.wizard_data = {
        "title": "Req",
        "description": "Desc",
        "type": "functional",
        "priority": "medium",
        "constraints": "",
    }
    stub_streamlit.button.return_value = True
    m = mock_open()
    with patch("builtins.open", m):
        WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 0
    assert stub_streamlit.session_state.wizard_data == {}