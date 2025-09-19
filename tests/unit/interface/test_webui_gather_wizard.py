import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Create a stub streamlit module for testing."""
    st = ModuleType("streamlit")
    class State(dict):
        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError as exc:
                raise AttributeError(name) from exc

        def __setattr__(self, name, value):
            self[name] = value

    st.session_state = State()
    st.text_input = MagicMock(return_value="Test Input")
    st.text_area = MagicMock(return_value="Test Area")
    st.selectbox = MagicMock(return_value="documentation")
    st.button = MagicMock(return_value=False)
    st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
    st.header = MagicMock()
    st.write = MagicMock()
    st.subheader = MagicMock()
    st.progress = MagicMock()
    st.spinner = MagicMock()
    st.spinner.return_value.__enter__ = MagicMock()
    st.spinner.return_value.__exit__ = MagicMock(return_value=False)
    st.experimental_rerun = MagicMock()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def mock_gather_requirements(monkeypatch):
    gather_mock = MagicMock()
    monkeypatch.setattr("devsynth.core.workflows.gather_requirements", gather_mock)
    import devsynth.interface.webui.rendering as rendering

    monkeypatch.setattr(rendering, "gather_requirements", gather_mock, raising=False)
    monkeypatch.setattr(
        "devsynth.interface.webui.gather_requirements", gather_mock, raising=False
    )
    return gather_mock


@pytest.mark.medium
def test_gather_wizard_start_button_not_clicked(
    stub_streamlit, mock_gather_requirements
):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.button.return_value = False
    WebUI()._gather_wizard()
    mock_gather_requirements.assert_not_called()
    stub_streamlit.button.assert_called_once()
    assert stub_streamlit.button.call_args.kwargs["key"] == "start_gather_wizard_button"


@pytest.mark.medium
def test_gather_wizard_finish_calls_gather_requirements(
    stub_streamlit, mock_gather_requirements
):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state = type(stub_streamlit.session_state)({
        "gather_wizard_current_step": 3,
        "gather_wizard_total_steps": 3,
        "gather_wizard_completed": False,
        "gather_wizard_wizard_started": True,
        "gather_wizard_resource_type": "documentation",
        "gather_wizard_resource_location": "/docs",
        "gather_wizard_resource_metadata": {"author": "A", "version": "1.0"},
    })

    def button_side_effect(label, key=None, **kwargs):
        return key == "finish_button"

    stub_streamlit.button.side_effect = button_side_effect
    ui = WebUI()
    ui._gather_wizard()
    mock_gather_requirements.assert_called_once_with(ui)
    assert stub_streamlit.experimental_rerun.called


@pytest.mark.medium
def test_gather_wizard_import_error(stub_streamlit, monkeypatch):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state = type(stub_streamlit.session_state)({
        "gather_wizard_current_step": 3,
        "gather_wizard_total_steps": 3,
        "gather_wizard_completed": False,
        "gather_wizard_wizard_started": True,
        "gather_wizard_resource_type": "documentation",
        "gather_wizard_resource_location": "/docs",
        "gather_wizard_resource_metadata": {"author": "A", "version": "1.0"},
    })
    stub_streamlit.button.side_effect = (
        lambda label, key=None, **kwargs: key == "finish_button"
    )
    import devsynth.interface.webui.rendering as rendering

    monkeypatch.setattr(webui, "gather_requirements", None, raising=False)
    monkeypatch.setattr(rendering, "gather_requirements", None, raising=False)
    ui = WebUI()
    ui.display_result = MagicMock()
    ui._gather_wizard()
    ui.display_result.assert_called_once()
    assert "ERROR importing gather_requirements" in ui.display_result.call_args[0][0]


@pytest.mark.medium
def test_gather_wizard_exception(stub_streamlit, mock_gather_requirements):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    stub_streamlit.session_state = type(stub_streamlit.session_state)({
        "gather_wizard_current_step": 3,
        "gather_wizard_total_steps": 3,
        "gather_wizard_completed": False,
        "gather_wizard_wizard_started": True,
        "gather_wizard_resource_type": "documentation",
        "gather_wizard_resource_location": "/docs",
        "gather_wizard_resource_metadata": {"author": "A", "version": "1.0"},
    })
    stub_streamlit.button.side_effect = (
        lambda label, key=None, **kwargs: key == "finish_button"
    )
    mock_gather_requirements.side_effect = RuntimeError("boom")
    ui = WebUI()
    ui.display_result = MagicMock()
    ui._gather_wizard()
    mock_gather_requirements.assert_called_once_with(ui)
    ui.display_result.assert_called_once()
    assert "ERROR processing resources" in ui.display_result.call_args[0][0]
