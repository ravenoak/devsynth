import sys
from types import ModuleType
from unittest.mock import MagicMock, call, patch

import pytest

pytestmark = [pytest.mark.fast]


class SessionState(dict):
    """A dictionary that also allows attribute access."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'dict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value


def _mock_streamlit():
    """Create a mock streamlit module for testing."""
    st = ModuleType("streamlit")
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.info = MagicMock()
    st.error = MagicMock()
    st.warning = MagicMock()
    st.success = MagicMock()
    st.header = MagicMock()
    st.subheader = MagicMock()
    st.text_input = MagicMock(return_value="t")
    st.selectbox = MagicMock(return_value="c")
    st.checkbox = MagicMock(return_value=True)
    st.empty = MagicMock(return_value=MagicMock())
    st.progress = MagicMock(return_value=MagicMock())
    st.container = MagicMock()
    st.container.return_value.__enter__ = MagicMock(return_value=MagicMock())
    st.container.return_value.__exit__ = MagicMock(return_value=None)
    st.set_page_config = MagicMock()
    st.components = ModuleType("components")
    st.components.v1 = ModuleType("v1")
    st.components.v1.html = MagicMock()
    st.session_state = SessionState()

    # Add missing Streamlit attributes
    st.expander = MagicMock()
    st.expander.return_value.__enter__ = MagicMock(return_value=MagicMock())
    st.expander.return_value.__exit__ = MagicMock(return_value=None)
    st.form_submit_button = MagicMock(return_value=False)
    st.form = MagicMock()
    st.form.return_value.__enter__ = MagicMock(return_value=MagicMock())
    st.form.return_value.__exit__ = MagicMock(return_value=None)
    st.sidebar = MagicMock()
    st.sidebar.selectbox = MagicMock(return_value="c")
    st.sidebar.checkbox = MagicMock(return_value=True)
    st.sidebar.text_input = MagicMock(return_value="t")
    st.sidebar.button = MagicMock(return_value=False)
    st.button = MagicMock(return_value=False)
    st.radio = MagicMock(return_value="option1")
    st.slider = MagicMock(return_value=50)
    st.file_uploader = MagicMock(return_value=None)
    st.divider = MagicMock()
    st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
    st.tabs = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
    st.spinner = MagicMock()
    st.spinner.return_value.__enter__ = MagicMock(return_value=MagicMock())
    st.spinner.return_value.__exit__ = MagicMock(return_value=None)
    st.code = MagicMock()
    st.experimental_rerun = MagicMock()

    return st


@pytest.fixture
def mock_streamlit(monkeypatch):
    """Fixture to mock streamlit for testing."""
    st = _mock_streamlit()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state


def test_webui_display_result_highlight_succeeds(mock_streamlit, clean_state):
    """Test that highlighted messages use st.info.

    ReqID: N/A"""
    import importlib

    from devsynth.interface import webui

    # Reload the module to ensure clean state
    importlib.reload(webui)

    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("Important message", highlight=True)
    mock_streamlit.info.assert_called_once_with("Important message")


def test_webui_display_result_error_raises_error(mock_streamlit):
    """Test that error messages use st.error.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("ERROR: Something went wrong", highlight=False)
    mock_streamlit.error.assert_called_once_with("ERROR: Something went wrong")


def test_webui_display_result_warning_succeeds(mock_streamlit):
    """Test that warning messages use st.warning.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("WARNING: Be careful", highlight=False)
    mock_streamlit.warning.assert_called_once_with("WARNING: Be careful")


def test_webui_display_result_success_succeeds(mock_streamlit):
    """Test that success messages use st.success.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("Task completed successfully", highlight=False)
    mock_streamlit.success.assert_called_once_with("Task completed successfully")


def test_webui_display_result_heading_succeeds(mock_streamlit):
    """Test that heading messages use st.header.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("# Heading", highlight=False)
    mock_streamlit.header.assert_called_once_with("Heading")


def test_webui_display_result_subheading_succeeds(mock_streamlit):
    """Test that subheading messages use st.subheader.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("## Subheading", highlight=False)
    mock_streamlit.subheader.assert_called_once_with("Subheading")


def test_webui_display_result_rich_markup_succeeds(mock_streamlit):
    """Test that Rich markup is converted to Markdown/HTML.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("[bold]Bold text[/bold]", highlight=False)
    mock_streamlit.markdown.assert_called_once_with(
        "**Bold text**", unsafe_allow_html=True
    )


def test_webui_display_result_normal_succeeds(mock_streamlit):
    """Test that normal messages use st.write.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    bridge.display_result("Normal message", highlight=False)
    mock_streamlit.write.assert_called_once_with("Normal message")


def test_webui_progress_indicator_succeeds(mock_streamlit):
    """Test the enhanced progress indicator.

    ReqID: N/A"""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    bridge = WebUI()
    progress = bridge.create_progress("Main task", total=100)
    status_container = mock_streamlit.empty.return_value
    status_container.markdown.assert_called_with("**Main task** - 0%")
    progress.update(advance=10, description="Updated task")
    status_container.markdown.assert_called_with("**Updated task** - 10%")
    subtask_id = progress.add_subtask("Subtask 1", 50)
    assert subtask_id == "subtask_0"
    progress.update_subtask(subtask_id, 25, "Updated subtask")
    progress.complete_subtask(subtask_id)
    progress.complete()
    mock_streamlit.success.assert_called_with("Completed: Updated task")
