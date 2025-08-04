import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def stub_streamlit(monkeypatch):
    """Provide a stubbed streamlit module for testing."""
    st = ModuleType("streamlit")

    class SS(dict):
        pass

    st.session_state = SS()
    st.header = MagicMock()
    st.write = MagicMock()
    st.progress = MagicMock()
    st.text_input = MagicMock(return_value="Title")
    st.text_area = MagicMock(return_value="Desc")
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


@pytest.mark.medium
def test_priority_persists_through_navigation(stub_streamlit):
    """Priority selection should persist when navigating steps."""
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
