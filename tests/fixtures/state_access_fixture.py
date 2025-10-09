"""
Test fixtures for state access and wizard state manager.

This module provides fixtures for testing the state_access module and
the WizardStateManager class with proper session state mocking.
"""

import pytest

from tests.fixtures.streamlit_mocks import StreamlitModule, StreamlitStub


class MockSessionState(dict):
    """A mock session state that behaves like both a dictionary and an object with attributes."""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        return None

    def __setattr__(self, name, value):
        self[name] = value


def create_mock_session_state():
    """Create a mock session state for testing."""
    return MockSessionState()


@pytest.fixture
def mock_session_state():
    """Create a mock session state for testing state access functions."""
    return create_mock_session_state()


@pytest.fixture
def mock_streamlit_for_state() -> StreamlitModule:
    """
    Create a mock streamlit module with session state for testing.

    This is similar to the mock_streamlit fixture in webui_wizard_state_fixture.py,
    but focused specifically on session state for testing state_access functions.
    """
    st = StreamlitStub()
    st.session_state = create_mock_session_state()
    return st


@pytest.fixture
def wizard_state_manager(mock_session_state):
    """
    Create a WizardStateManager instance for testing.

    Args:
        mock_session_state: The mock session state fixture

    Returns:
        A tuple containing the WizardStateManager instance and the mock session state
    """
    # Import WizardStateManager here to avoid circular imports
    from devsynth.interface.wizard_state_manager import WizardStateManager

    # Initialize the wizard state manager with a name, number of steps, and initial state
    wizard_name = "test_wizard"
    steps = 3
    initial_state = {"step1_data": "", "step2_data": "", "step3_data": ""}

    # Create the WizardStateManager instance
    manager = WizardStateManager(mock_session_state, wizard_name, steps, initial_state)

    # Return the manager and the mock session state
    return manager, mock_session_state


@pytest.fixture
def gather_wizard_state_manager(mock_session_state):
    """
    Create a WizardStateManager instance specifically for testing the gather wizard.

    Args:
        mock_session_state: The mock session state fixture

    Returns:
        A tuple containing the WizardStateManager instance and the mock session state
    """
    # Import WizardStateManager here to avoid circular imports
    from devsynth.interface.wizard_state_manager import WizardStateManager

    # Initialize the wizard state manager with a name, number of steps, and initial state
    wizard_name = "gather_wizard"
    steps = 3
    initial_state = {
        "resource_type": "",
        "resource_location": "",
        "resource_metadata": {},
    }

    # Create the WizardStateManager instance
    manager = WizardStateManager(mock_session_state, wizard_name, steps, initial_state)

    # Return the manager and the mock session state
    return manager, mock_session_state


def simulate_wizard_manager_navigation(manager, navigation_steps):
    """
    Simulate navigation through a wizard with the given steps using a WizardStateManager.

    Args:
        manager: The WizardStateManager instance
        navigation_steps: A list of navigation actions ('next', 'previous', 'goto_X')

    Returns:
        The final step number
    """
    for action in navigation_steps:
        if action == "next":
            manager.next_step()
        elif action == "previous":
            manager.previous_step()
        elif action.startswith("goto_"):
            step = int(action.split("_")[1])
            manager.go_to_step(step)

    return manager.get_current_step()


def set_wizard_manager_data(manager, step_data):
    """
    Set data for specific steps in the wizard using a WizardStateManager.

    Args:
        manager: The WizardStateManager instance
        step_data: A dictionary mapping step keys to values
    """
    for key, value in step_data.items():
        manager.set_value(key, value)
