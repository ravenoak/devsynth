"""
Standardized mocking utilities for WebUI components.

This module provides standardized mocking utilities for WebUI components that can be
used consistently across all tests. It includes:

1. A standardized mock Streamlit implementation
2. Fixtures for mocking WebUI components with WizardState integration
3. Helper functions for simulating user interactions with WebUI components

Usage:
    from tests.fixtures.webui_test_utils import (
        mock_streamlit,
        mock_webui,
        mock_wizard_state,
        simulate_button_click,
        simulate_form_submission,
        simulate_wizard_navigation
    )
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple, Union
from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from tests.fixtures.streamlit_mocks import StreamlitModule, StreamlitStub
from tests.fixtures.webui_bridge_stub import install_streamlit_stub


class DummyForm:
    """Simple context manager used for mock Streamlit components."""

    def __init__(self, submitted: bool = True):
        self.submitted = submitted

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def form_submit_button(self, *_args, **_kwargs):  # pragma: no cover - simple mock
        return self.submitted

    def button(self, *_args, **_kwargs):  # pragma: no cover - simple mock
        return self.submitted


def create_mock_streamlit() -> StreamlitModule:
    """
    Create a standardized mock Streamlit implementation.

    This function creates a mock Streamlit module with all the commonly used
    Streamlit functions mocked. It includes proper session state handling and
    form handling.

    Returns:
        A mock Streamlit module
    """
    st = StreamlitStub()

    # Mock input functions
    st.button.return_value = False
    st.text_input.return_value = ""
    st.text_area.return_value = ""
    st.selectbox.return_value = ""
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
    st.toggle.return_value = True

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
    st.progress = MagicMock()
    st.tabs = MagicMock(return_value=[DummyForm() for _ in range(5)])

    # Mock layout functions
    col1_mock = MagicMock()
    col1_mock.button = MagicMock(return_value=False)
    col2_mock = MagicMock()
    col2_mock.button = MagicMock(return_value=False)
    col3_mock = MagicMock()
    col3_mock.button = MagicMock(return_value=False)
    st.columns = MagicMock(return_value=[col1_mock, col2_mock, col3_mock])

    # Mock container functions
    container_mock = MagicMock()
    container_mock.button = MagicMock(return_value=False)
    container_mock.text_input = MagicMock(return_value="")
    container_mock.text_area = MagicMock(return_value="")
    container_mock.selectbox = MagicMock(return_value="")
    st.container = MagicMock(return_value=container_mock)

    # Mock expander functions
    expander_mock = MagicMock()
    expander_mock.button = MagicMock(return_value=False)
    expander_mock.text_input = MagicMock(return_value="")
    expander_mock.text_area = MagicMock(return_value="")
    expander_mock.selectbox = MagicMock(return_value="")
    expander_mock.__enter__ = MagicMock(return_value=expander_mock)
    expander_mock.__exit__ = MagicMock(return_value=None)
    st.expander = MagicMock(return_value=expander_mock)

    # Mock form functions
    form_mock = MagicMock()
    form_mock.button = MagicMock(return_value=False)
    form_mock.text_input = MagicMock(return_value="")
    form_mock.text_area = MagicMock(return_value="")
    form_mock.selectbox = MagicMock(return_value="")
    form_mock.__enter__ = MagicMock(return_value=form_mock)
    form_mock.__exit__ = MagicMock(return_value=None)
    st.form = MagicMock(return_value=form_mock)
    st.form_submit_button.return_value = False

    # Mock spinner functions
    spinner_mock = MagicMock()
    spinner_mock.__enter__ = MagicMock(return_value=spinner_mock)
    spinner_mock.__exit__ = MagicMock(return_value=None)
    st.spinner = MagicMock(return_value=spinner_mock)

    # Mock sidebar functions
    sidebar_mock = MagicMock()
    sidebar_mock.button = MagicMock(return_value=False)
    sidebar_mock.text_input = MagicMock(return_value="")
    sidebar_mock.text_area = MagicMock(return_value="")
    sidebar_mock.selectbox = MagicMock(return_value="")
    sidebar_mock.radio = MagicMock(return_value="")
    sidebar_mock.title = MagicMock()
    sidebar_mock.header = MagicMock()
    sidebar_mock.subheader = MagicMock()
    sidebar_mock.markdown = MagicMock()
    st.sidebar = sidebar_mock

    # Mock experimental functions
    st.experimental_rerun = MagicMock()

    # Mock components
    st.components.v1.html = MagicMock(return_value=None)

    # Mock set_page_config and divider
    st.set_page_config = MagicMock()
    st.divider = MagicMock()

    return st


@pytest.fixture
def mock_streamlit(monkeypatch: pytest.MonkeyPatch):
    """
    Fixture that provides a standardized mock Streamlit implementation.

    This fixture creates a mock Streamlit module and patches it in the
    webui_state and webui modules to ensure consistent behavior.

    Returns:
        A mock Streamlit module
    """
    # Create the mock Streamlit module
    mock_st = create_mock_streamlit()
    install_streamlit_stub(mock_st, monkeypatch)
    monkeypatch.setattr("devsynth.interface.webui_state.st", mock_st, raising=False)
    yield mock_st


@pytest.fixture
def mock_webui(mock_streamlit):
    """
    Fixture that provides a mock WebUI instance.

    This fixture creates a mock WebUI instance with the mock_streamlit fixture
    and patches the necessary dependencies.

    Args:
        mock_streamlit: The mock Streamlit module from the mock_streamlit fixture

    Returns:
        A tuple of (mock WebUI instance, context dictionary)
    """
    # Create a context dictionary to store test state
    context = {
        "st": mock_streamlit,
        "buttons_clicked": set(),
        "form_submitted": False,
        "input_values": {},
    }

    # Import the WebUI class after patching Streamlit
    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    # Create a WebUI instance
    ui = webui.WebUI()

    # Mock the display_result method
    original_display_result = ui.display_result
    ui.display_result = MagicMock(wraps=original_display_result)

    # Add the WebUI instance to the context
    context["ui"] = ui
    context["webui"] = webui

    # Mock CLI commands
    cli_mock = ModuleType("devsynth.application.cli")
    command_names = [
        "init_cmd",
        "spec_cmd",
        "test_cmd",
        "code_cmd",
        "run_pipeline_cmd",
        "doctor_cmd",
        "edrr_cycle_cmd",
        "config_cmd",
        "inspect_cmd",
        "align_cmd",
        "inspect_code_cmd",
        "alignment_metrics_cmd",
        "validate_manifest_cmd",
        "validate_metadata_cmd",
        "test_metrics_cmd",
        "generate_docs_cmd",
        "ingest_cmd",
        "apispec_cmd",
        "analyze_manifest_cmd",
        "inspect_config_cmd",
    ]
    for name in command_names:
        setattr(cli_mock, name, MagicMock())

    # Patch the CLI module
    with patch.dict("sys.modules", {"devsynth.application.cli": cli_mock}):
        # Add the CLI mock to the context
        context["cli"] = cli_mock

        yield ui, context


@pytest.fixture
def mock_wizard_state(mock_streamlit):
    """
    Fixture that provides a mock WizardState instance.

    This fixture creates a mock WizardState instance with the mock_streamlit fixture
    and initializes it with default values.

    Args:
        mock_streamlit: The mock Streamlit module from the mock_streamlit fixture

    Returns:
        A tuple of (WizardState instance, context dictionary)
    """
    # Import WizardState after patching Streamlit
    from devsynth.interface.webui_state import WizardState

    # Create a context dictionary to store test state
    context = {
        "st": mock_streamlit,
        "buttons_clicked": set(),
        "form_submitted": False,
        "input_values": {},
    }

    # Initialize the wizard state with default values
    wizard_name = "test_wizard"
    steps = 3
    initial_state = {"step1_data": "", "step2_data": "", "step3_data": ""}

    # Create the WizardState instance
    state = WizardState(wizard_name, steps, initial_state)

    # Add the WizardState instance to the context
    context["wizard_state"] = state

    yield state, context


def simulate_button_click(context: dict[str, Any], button_key: str) -> None:
    """
    Simulate clicking a button in the WebUI.

    This function simulates clicking a button in the WebUI by setting up the
    mock Streamlit button function to return True for the specified button key.

    Args:
        context: The context dictionary from the mock_webui or mock_wizard_state fixture
        button_key: The key of the button to click
    """
    # Add the button to the set of clicked buttons
    context["buttons_clicked"].add(button_key)

    # Set up the button mock to return True for the specified button key
    def button_side_effect(label, key=None, **kwargs):
        return key == button_key and key in context["buttons_clicked"]

    # Apply the side effect to the button mock
    context["st"].button.side_effect = button_side_effect

    # Apply the side effect to column button mocks if they exist
    if hasattr(context["st"], "columns") and context["st"].columns.return_value:
        for col in context["st"].columns.return_value:
            col.button.side_effect = button_side_effect


def simulate_form_submission(context: dict[str, Any], form_key: str) -> None:
    """
    Simulate submitting a form in the WebUI.

    This function simulates submitting a form in the WebUI by setting up the
    mock Streamlit form_submit_button function to return True for the specified form key.

    Args:
        context: The context dictionary from the mock_webui or mock_wizard_state fixture
        form_key: The key of the form to submit
    """
    # Set the form_submitted flag to True
    context["form_submitted"] = True

    # Set up the form_submit_button mock to return True
    context["st"].form_submit_button.return_value = True

    # Set up the form mock to return a form with a submit button that returns True
    form_mock = MagicMock()
    form_mock.form_submit_button = MagicMock(return_value=True)
    form_mock.__enter__ = MagicMock(return_value=form_mock)
    form_mock.__exit__ = MagicMock(return_value=None)

    # Apply the form mock
    context["st"].form.return_value = form_mock


def simulate_input(
    context: dict[str, Any], input_type: str, label: str, value: Any
) -> None:
    """
    Simulate entering input in the WebUI.

    This function simulates entering input in the WebUI by setting up the
    mock Streamlit input function to return the specified value for the specified label.

    Args:
        context: The context dictionary from the mock_webui or mock_wizard_state fixture
        input_type: The type of input (text_input, text_area, selectbox, etc.)
        label: The label of the input field
        value: The value to enter
    """
    # Add the input value to the dictionary of input values
    context["input_values"][(input_type, label)] = value

    # Set up the input mock to return the specified value for the specified label
    def input_side_effect(input_label, **kwargs):
        if (
            input_label == label
            and (input_type, input_label) in context["input_values"]
        ):
            return context["input_values"][(input_type, input_label)]
        return kwargs.get("value", "")

    # Apply the side effect to the input mock
    if hasattr(context["st"], input_type):
        getattr(context["st"], input_type).side_effect = input_side_effect


def simulate_wizard_navigation(wizard_state, navigation_steps: list[str]) -> int:
    """
    Simulate navigation through a wizard.

    This function simulates navigation through a wizard by calling the appropriate
    methods on the WizardState instance.

    Args:
        wizard_state: The WizardState instance
        navigation_steps: A list of navigation actions ('next', 'previous', 'goto_X')

    Returns:
        The final step number
    """
    for action in navigation_steps:
        if action == "next":
            wizard_state.next_step()
        elif action == "previous":
            wizard_state.previous_step()
        elif action.startswith("goto_"):
            step = int(action.split("_")[1])
            wizard_state.go_to_step(step)

    return wizard_state.get_current_step()


def set_wizard_data(wizard_state, data: dict[str, Any]) -> None:
    """
    Set data in a wizard.

    This function sets data in a wizard by calling the set method on the
    WizardState instance for each key-value pair in the data dictionary.

    Args:
        wizard_state: The WizardState instance
        data: A dictionary mapping keys to values
    """
    for key, value in data.items():
        wizard_state.set(key, value)


def get_wizard_data(wizard_state, keys: list[str]) -> dict[str, Any]:
    """
    Get data from a wizard.

    This function gets data from a wizard by calling the get method on the
    WizardState instance for each key in the keys list.

    Args:
        wizard_state: The WizardState instance
        keys: A list of keys to get

    Returns:
        A dictionary mapping keys to values
    """
    return {key: wizard_state.get(key) for key in keys}


def assert_wizard_step(wizard_state, expected_step: int) -> None:
    """
    Assert that the wizard is on the expected step.

    This function asserts that the wizard is on the expected step by checking
    the current step of the WizardState instance.

    Args:
        wizard_state: The WizardState instance
        expected_step: The expected step number
    """
    assert (
        wizard_state.get_current_step() == expected_step
    ), f"Expected wizard to be on step {expected_step}, but it's on step {wizard_state.get_current_step()}"


def assert_wizard_completed(wizard_state, expected_completed: bool = True) -> None:
    """
    Assert that the wizard is completed or not completed.

    This function asserts that the wizard is completed or not completed by checking
    the completion status of the WizardState instance.

    Args:
        wizard_state: The WizardState instance
        expected_completed: Whether the wizard is expected to be completed
    """
    assert (
        wizard_state.is_completed() == expected_completed
    ), f"Expected wizard completed status to be {expected_completed}, but it's {wizard_state.is_completed()}"


@pytest.fixture
def webui_context(mock_webui):
    """Convenience fixture returning only the WebUI context."""

    _, context = mock_webui
    return context
