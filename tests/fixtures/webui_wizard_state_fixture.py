"""
Test fixtures for WebUI wizard state management.

This module provides fixtures for testing WebUI wizards with proper state management.
It uses the WizardState class from webui_state.py to ensure consistent state
persistence between wizard steps.
"""

from unittest.mock import MagicMock, patch

import pytest

from tests.fixtures.streamlit_mocks import StreamlitModule, StreamlitStub


def create_mock_streamlit() -> StreamlitModule:
    """Create a mock streamlit module with session state for testing."""
    st = StreamlitStub()

    # Mock common streamlit functions
    st.button.return_value = False
    st.text_input = MagicMock(
        side_effect=lambda *args, **kwargs: kwargs.get("value", "")
    )
    st.text_area = MagicMock(
        side_effect=lambda *args, **kwargs: kwargs.get("value", "")
    )

    def _selectbox_side_effect(*args, **kwargs):
        options = []
        if len(args) > 1:
            options = list(args[1])
        elif "options" in kwargs:
            options = list(kwargs["options"])

        index = kwargs.get("index", 0)
        if not options:
            return ""
        try:
            return options[index]
        except Exception:
            return options[0]

    st.selectbox = MagicMock(side_effect=_selectbox_side_effect)
    st.multiselect.return_value = []
    st.checkbox.return_value = False
    st.radio.return_value = ""
    st.number_input.return_value = 0
    st.slider.return_value = 0
    st.select_slider.return_value = ""
    st.date_input.return_value = None
    st.time_input.return_value = None
    st.file_uploader.return_value = None
    st.color_picker.return_value = ""

    # Mock display functions
    st.write = MagicMock()
    st.markdown = MagicMock()
    st.header = MagicMock()
    st.subheader = MagicMock()
    st.caption = MagicMock()
    st.code = MagicMock()
    st.error = MagicMock()
    st.warning = MagicMock()
    st.info = MagicMock()
    st.success = MagicMock()

    # Mock layout functions
    st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    st.expander = MagicMock()
    st.container = MagicMock()
    st.sidebar = MagicMock()
    st.sidebar.button = MagicMock(return_value=False)

    # Mock progress functions
    st.progress = MagicMock()
    st.spinner = MagicMock()
    st.spinner.return_value.__enter__ = MagicMock()
    st.spinner.return_value.__exit__ = MagicMock()

    # Mock form functions
    st.form = MagicMock()
    st.form.return_value.__enter__ = MagicMock()
    st.form.return_value.__exit__ = MagicMock()
    st.form_submit_button = MagicMock(return_value=False)

    return st


@pytest.fixture
def mock_streamlit():
    """
    Create a mock streamlit module and patch it in the webui_state and webui modules.

    This ensures that both the WizardState class and the WebUI class use our mock
    streamlit module instead of the real one.
    """
    # Create the mock streamlit module
    mock_st = create_mock_streamlit()

    # Add experimental_rerun method to mock streamlit
    mock_st.experimental_rerun = MagicMock()

    # Patch the streamlit module in both webui_state and webui modules
    with (
        patch("devsynth.interface.webui_state.st", mock_st),
        patch("devsynth.interface.webui.st", mock_st),
    ):
        yield mock_st


@pytest.fixture
def wizard_state(mock_streamlit):
    """Create a WizardState instance for testing wizards with multiple steps."""
    # Import WizardState after patching streamlit to ensure it uses our mock
    from devsynth.interface.webui_state import WizardState

    # Initialize the wizard state with a name, number of steps, and initial state
    wizard_name = "test_wizard"
    steps = 3
    initial_state = {"step1_data": "", "step2_data": "", "step3_data": ""}

    # Create the WizardState instance
    state = WizardState(wizard_name, steps, initial_state)

    # Return the state and the mock streamlit module
    return state, mock_streamlit


@pytest.fixture
def gather_wizard_state(mock_streamlit):
    """Create a WizardState instance specifically for testing the gather wizard."""
    # Import WizardState after patching streamlit to ensure it uses our mock
    from devsynth.interface.webui_state import WizardState

    # Initialize the wizard state with a name, number of steps, and initial state
    wizard_name = "gather_wizard"
    steps = 3
    initial_state = {
        "resource_type": "",
        "resource_location": "",
        "resource_metadata": {},
    }

    # Create the WizardState instance
    state = WizardState(wizard_name, steps, initial_state)

    # Return the state and the mock streamlit module
    return state, mock_streamlit


def simulate_wizard_navigation(state, mock_streamlit, navigation_steps):
    """
    Simulate navigation through a wizard with the given steps.

    Args:
        state: The WizardState instance
        mock_streamlit: The mock streamlit module
        navigation_steps: A list of navigation actions ('next', 'previous', 'goto_X')

    Returns:
        The final step number
    """
    for action in navigation_steps:
        if action == "next":
            state.next_step()
        elif action == "previous":
            state.previous_step()
        elif action.startswith("goto_"):
            step = int(action.split("_")[1])
            state.go_to_step(step)

    return state.get_current_step()


def set_wizard_data(state, step_data):
    """
    Set data for specific steps in the wizard.

    Args:
        state: The WizardState instance
        step_data: A dictionary mapping step keys to values
    """
    for key, value in step_data.items():
        state.set(key, value)
