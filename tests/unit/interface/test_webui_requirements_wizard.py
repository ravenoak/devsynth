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


def test_requirements_wizard_initial_state_succeeds(stub_streamlit):
    """Test that the requirements wizard initializes with the correct state.

    ReqID: N/A"""
    import importlib
    import devsynth.interface.webui as webui

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


def test_requirements_wizard_step_navigation_succeeds(stub_streamlit):
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


def test_requirements_wizard_preserves_existing_state(stub_streamlit):
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


def test_requirements_wizard_save_requirements_succeeds(stub_streamlit, monkeypatch):
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
    with patch("builtins.open", m):
        result = webui_instance._requirements_wizard()
    webui_instance.display_result.assert_called_once()
    assert "[green]" in webui_instance.display_result.call_args[0][0]
    assert result == expected_data


def test_requirements_wizard_different_steps_succeeds(stub_streamlit):
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


def test_requirements_wizard_string_step_succeeds(stub_streamlit):
    """Wizard should handle string step values."""
    import importlib
    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state.wizard_step = "2"
    WebUI()._requirements_wizard()
    assert stub_streamlit.session_state.wizard_step == 2


def test_requirements_wizard_error_handling_raises_error(stub_streamlit, monkeypatch):
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
