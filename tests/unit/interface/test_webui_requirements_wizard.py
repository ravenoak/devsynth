import sys
from types import ModuleType
from unittest.mock import MagicMock, mock_open, patch

import pytest


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Create a stub streamlit module for testing."""
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.header = MagicMock()
    st.write = MagicMock()
    st.progress = MagicMock()
    st.text_input = MagicMock(return_value="Title")
    st.text_area = MagicMock(return_value="Description")
    st.selectbox = MagicMock(return_value="functional")
    st.button = MagicMock(return_value=False)
    st.columns = MagicMock(
        return_value=(
            MagicMock(button=MagicMock(return_value=False)),
            MagicMock(button=MagicMock(return_value=False)),
            MagicMock(button=MagicMock(return_value=False)),
        )
    )
    monkeypatch.setitem(sys.modules, "streamlit", st)
    return st


@pytest.fixture
def clean_state():
    """Set up and tear down a clean state for tests."""
    yield


@pytest.mark.medium
def test_requirements_wizard_initialization(stub_streamlit, clean_state):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    WebUI()._requirements_wizard()
    assert stub_streamlit.header.called
    assert stub_streamlit.progress.called
    assert stub_streamlit.session_state["requirements_wizard_current_step"] == 1


@pytest.mark.medium
def test_requirements_wizard_step_navigation_succeeds(stub_streamlit, clean_state):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    col1 = MagicMock(button=MagicMock(return_value=False))
    col2 = MagicMock(button=MagicMock(return_value=True))
    col3 = MagicMock(button=MagicMock(return_value=False))
    stub_streamlit.columns.return_value = (col1, col2, col3)

    ui = WebUI()
    ui._requirements_wizard()
    assert stub_streamlit.session_state["requirements_wizard_current_step"] == 2


@pytest.mark.medium
def test_requirements_wizard_save_requirements_succeeds(stub_streamlit, clean_state):
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    ui = WebUI()
    col1 = MagicMock(button=MagicMock(return_value=False))
    col2 = MagicMock(button=MagicMock(return_value=True))
    col3 = MagicMock(button=MagicMock(return_value=False))
    stub_streamlit.columns.return_value = (col1, col2, col3)
    stub_streamlit.selectbox.side_effect = ["functional", "medium"]
    ui._requirements_wizard()
    ui._requirements_wizard()
    ui._requirements_wizard()
    ui._requirements_wizard()
    col2.button.return_value = True
    m = mock_open()
    with patch("builtins.open", m):
        result = ui._requirements_wizard()
    assert result["title"] == "Title"
    assert stub_streamlit.session_state["requirements_wizard_current_step"] == 1


@pytest.mark.medium
def test_validate_requirements_step():
    from devsynth.interface.webui import WebUI
    from devsynth.interface.webui_state import WizardState

    ui = WebUI()
    state = WizardState("req", 5)
    assert not ui._validate_requirements_step(state, 1)
    state.set("title", "T")
    assert ui._validate_requirements_step(state, 1)


@pytest.mark.medium
def test_handle_requirements_navigation_next(stub_streamlit):
    from devsynth.interface.webui import WebUI

    ui = WebUI()
    manager = MagicMock()
    state = MagicMock()
    state.get_total_steps.return_value = 5
    state.get_current_step.return_value = 1
    stub_streamlit.columns.return_value = (
        MagicMock(button=MagicMock(return_value=False)),
        MagicMock(button=MagicMock(return_value=True)),
        MagicMock(button=MagicMock(return_value=False)),
    )
    ui._handle_requirements_navigation(manager, state)
    manager.next_step.assert_called_once()


@pytest.mark.medium
def test_save_requirements_writes_file(stub_streamlit):
    from devsynth.interface.webui import WebUI

    ui = WebUI()
    ui.display_result = MagicMock()
    manager = MagicMock()
    manager.get_value.side_effect = lambda key, default=None: {
        "title": "Req",
        "description": "Desc",
        "type": "functional",
        "priority": "medium",
        "constraints": "c1,c2",
    }[key]
    manager.set_completed.return_value = True
    manager.reset_wizard_state.return_value = True
    m = mock_open()
    with patch("builtins.open", m):
        result = ui._save_requirements(manager)
    assert result["title"] == "Req"
    manager.set_completed.assert_called_once_with(True)
    manager.reset_wizard_state.assert_called_once()


@pytest.mark.medium
def test_priority_persists_through_navigation(stub_streamlit):
    """Priority selection should persist when navigating steps."""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    st = stub_streamlit
    ui = WebUI()

    # Initialize wizard
    ui._requirements_wizard()

    # Simulate priority selection and navigation
    st.session_state["requirements_wizard_priority"] = "high"
    st.session_state["requirements_wizard_current_step"] = 5
    ui._requirements_wizard()
    st.session_state["requirements_wizard_current_step"] = 4
    ui._requirements_wizard()

    assert st.session_state["requirements_wizard_priority"] == "high"


@pytest.mark.medium
def test_title_and_description_persist(stub_streamlit):
    """Title and description should persist across navigation."""
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)
    from devsynth.interface.webui import WebUI

    st = stub_streamlit
    ui = WebUI()

    st.text_input.return_value = "My Title"
    ui._requirements_wizard()  # step 1

    # Simulate description being set on step 2
    st.session_state["requirements_wizard_description"] = "My Description"

    # Return to step 1 and ensure values persist
    st.session_state["requirements_wizard_current_step"] = 1
    ui._requirements_wizard()

    assert st.session_state["requirements_wizard_title"] == "My Title"
    assert st.session_state["requirements_wizard_description"] == "My Description"
