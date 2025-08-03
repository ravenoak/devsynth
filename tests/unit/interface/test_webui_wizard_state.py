"""
Tests for WebUI wizard state management.

This module demonstrates how to use the wizard_state_fixture to test
wizards with proper state persistence between steps.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch
from types import ModuleType
from pathlib import Path

from devsynth.interface.wizard_state_manager import WizardStateManager

# Import the fixtures
fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
sys.path.insert(0, str(fixtures_path))
try:
    from webui_wizard_state_fixture import ( mock_streamlit, wizard_state, gather_wizard_state, simulate_wizard_navigation, set_wizard_data )
except ImportError:
    # For debugging import issues
    print(f"Fixtures path: {fixtures_path}")
    print(f"Fixtures path exists: {fixtures_path.exists()}")
    print(f"Files in fixtures directory: {list(fixtures_path.glob('*.py'))}")
    raise

@pytest.mark.medium

@pytest.fixture
def clean_state():
    # Set up clean state
    yield
    # Clean up state

def test_function(clean_state, wizard_state):
    """Test that the wizard state is properly initialized."""
    state, mock_st = wizard_state
    
    # Check that the state has the correct properties
    assert state.page_name == "test_wizard"
    assert state.get_total_steps() == 3
    assert state.get_current_step() == 1
    assert state.is_completed() is False
    
    # Check that the initial state was set
    assert state.get("step1_data") == ""
    assert state.get("step2_data") == ""
    assert state.get("step3_data") == ""

@pytest.mark.medium
def test_wizard_state_navigation(wizard_state):
    """Test navigation through wizard steps."""
    state, mock_st = wizard_state
    
    # Start at step 1
    assert state.get_current_step() == 1
    
    # Move to step 2
    state.next_step()
    assert state.get_current_step() == 2
    
    # Move to step 3
    state.next_step()
    assert state.get_current_step() == 3
    
    # Try to move past the last step (should stay at step 3)
    state.next_step()
    assert state.get_current_step() == 3
    
    # Move back to step 2
    state.previous_step()
    assert state.get_current_step() == 2
    
    # Move back to step 1
    state.previous_step()
    assert state.get_current_step() == 1
    
    # Try to move before the first step (should stay at step 1)
    state.previous_step()
    assert state.get_current_step() == 1
    
    # Go directly to step 3
    state.go_to_step(3)
    assert state.get_current_step() == 3
    
    # Try to go to an invalid step (should be normalized to a valid step)
    state.go_to_step(5)
    assert state.get_current_step() == 3
    
    state.go_to_step(0)
    assert state.get_current_step() == 1

@pytest.mark.medium
def test_wizard_state_data_persistence(wizard_state):
    """Test that data persists between wizard steps."""
    state, mock_st = wizard_state
    
    # Set data for step 1
    state.set("step1_data", "Step 1 Value")
    
    # Move to step 2
    state.next_step()
    
    # Set data for step 2
    state.set("step2_data", "Step 2 Value")
    
    # Move to step 3
    state.next_step()
    
    # Set data for step 3
    state.set("step3_data", "Step 3 Value")
    
    # Move back to step 1
    state.go_to_step(1)
    
    # Check that all data is still there
    assert state.get("step1_data") == "Step 1 Value"
    assert state.get("step2_data") == "Step 2 Value"
    assert state.get("step3_data") == "Step 3 Value"

@pytest.mark.medium
def test_wizard_state_completion(wizard_state):
    """Test setting the wizard completion status."""
    state, mock_st = wizard_state
    
    
    # Initially not completed
    assert state.is_completed() is False
    
    # Set as completed
    state.set_completed(True)
    assert state.is_completed() is True
    
    # Set as not completed
    state.set_completed(False)
    assert state.is_completed() is False

@pytest.mark.medium
def test_wizard_state_reset(wizard_state):
    """Test resetting the wizard state."""
    state, mock_st = wizard_state
    
    # Set some data
    state.set("step1_data", "Step 1 Value")
    state.set("step2_data", "Step 2 Value")
    state.next_step()
    state.set_completed(True)
    
    # Reset the state
    state.reset()
    
    # Check that everything is back to initial values
    assert state.get_current_step() == 1
    assert state.is_completed() is False
    assert state.get("step1_data") == ""
    assert state.get("step2_data") == ""

@pytest.mark.medium
def test_gather_wizard_state_initialization(gather_wizard_state):
    """Test that the gather wizard state is properly initialized."""
    state, mock_st = gather_wizard_state
    
    # Check that the state has the correct properties
    assert state.page_name == "gather_wizard"
    assert state.get_total_steps() == 3
    assert state.get_current_step() == 1
    assert state.is_completed() is False
    
    # Check that the initial state was set
    assert state.get("resource_type") == ""
    assert state.get("resource_location") == ""
    assert isinstance(state.get("resource_metadata"), dict)

@pytest.mark.medium
def test_gather_wizard_workflow(gather_wizard_state):
    """Test a complete gather wizard workflow with state persistence."""
    state, mock_st = gather_wizard_state
    
    # Step 1: Set resource type
    assert state.get_current_step() == 1
    state.set("resource_type", "documentation")
    
    # Move to step 2
    state.next_step()
    assert state.get_current_step() == 2
    
    # Step 2: Set resource location
    state.set("resource_location", "/path/to/docs")
    
    # Move to step 3
    state.next_step()
    assert state.get_current_step() == 3
    
    # Step 3: Set resource metadata
    metadata = {
        "author": "Test User",
        "version": "1.0",
        "tags": ["test", "documentation"]
    }
    state.set("resource_metadata", metadata)
    
    # Complete the wizard
    state.set_completed(True)
    
    # Check that all data is still there
    assert state.get("resource_type") == "documentation"
    assert state.get("resource_location") == "/path/to/docs"
    assert state.get("resource_metadata") == metadata
    assert state.is_completed() is True

@pytest.mark.medium
def test_simulate_wizard_navigation(gather_wizard_state):
    """Test the simulate_wizard_navigation helper function."""
    state, mock_st = gather_wizard_state
    
    # Define a navigation sequence
    navigation_steps = ['next', 'next', 'previous', 'next', 'goto_1', 'next']
    
    # Simulate the navigation
    final_step = simulate_wizard_navigation(state, mock_st, navigation_steps)
    
    # Check the final step
    assert final_step == 2
    assert state.get_current_step() == 2

@pytest.mark.medium
def test_set_wizard_data(gather_wizard_state):
    """Test the set_wizard_data helper function."""
    state, mock_st = gather_wizard_state
    
    # Define data for multiple steps
    step_data = {
        "resource_type": "code",
        "resource_location": "/path/to/code",
        "resource_metadata": {
            "language": "Python",
            "lines": 1000
        }
    }
    
    # Set the data
    set_wizard_data(state, step_data)
    
    # Check that all data was set
    assert state.get("resource_type") == "code"
    assert state.get("resource_location") == "/path/to/code"
    assert state.get("resource_metadata") == {
        "language": "Python",
        "lines": 1000
    }


@pytest.mark.medium
def test_manager_clears_temp_state(mock_streamlit):
    """Ensure temporary state keys are removed by the manager."""
    manager = WizardStateManager(mock_streamlit.session_state, "temp", 1)
    mock_streamlit.session_state["temp_key"] = "value"
    manager.clear_temporary_state(["temp_key"])
    assert "temp_key" not in mock_streamlit.session_state

@pytest.mark.medium
def test_wizard_state_in_streamlit_context(gather_wizard_state):
    """Test using the wizard state in a simulated Streamlit context."""
    state, mock_st = gather_wizard_state
    
    # Track which buttons should be clicked
    clicked_buttons = set()
    
    # Mock Streamlit UI elements with controlled button behavior
    def mock_button(text, key=None, **kwargs):
        button_id = f"{text}_{key}"
        return button_id in clicked_buttons
    
    mock_st.button.side_effect = mock_button
    
    # Simulate a Streamlit app with wizard state
    def run_wizard_step():
        current_step = state.get_current_step()
        
        if current_step == 1:
            mock_st.header("Step 1: Resource Type")
            resource_type = mock_st.selectbox( "Select resource type", ["documentation", "code", "data"], key="resource_type_select" )
            state.set("resource_type", resource_type)
            
        elif current_step == 2:
            mock_st.header("Step 2: Resource Location")
            resource_location = mock_st.text_input( "Enter resource location", key="resource_location_input" )
            state.set("resource_location", resource_location)
            
        elif current_step == 3:
            mock_st.header("Step 3: Resource Metadata")
            author = mock_st.text_input("Author", key="author_input")
            version = mock_st.text_input("Version", key="version_input")
            tags = mock_st.text_input("Tags (comma-separated)", key="tags_input")
            
            metadata = {
                "author": author,
                "version": version,
                "tags": tags.split(",") if tags else []
            }
            state.set("resource_metadata", metadata)
        
        # Navigation buttons
        col1, col2 = mock_st.columns(2)
        
        with col1:
            if current_step > 1 and mock_st.button("Previous", key=f"prev_step_{current_step}"):
                state.previous_step()
                
        with col2:
            if current_step < state.get_total_steps():
                if mock_st.button("Next", key=f"next_step_{current_step}"):
                    state.next_step()
            else:
                if mock_st.button("Finish", key="finish_button"):
                    state.set_completed(True)
    
    # Step 1: Set resource type
    mock_st.selectbox.return_value = "documentation"
    run_wizard_step()
    
    # Check that the state was updated
    assert state.get("resource_type") == "documentation"
    assert state.get_current_step() == 1
    
    # Simulate clicking the Next button for step 1
    clicked_buttons.add(f"Next_next_step_1")
    run_wizard_step()
    
    # Check that we moved to step 2
    assert state.get_current_step() == 2
    
    # Step 2: Set resource location
    mock_st.text_input.return_value = "/path/to/docs"
    # Clear clicked buttons to ensure no automatic advancement
    clicked_buttons.clear()
    run_wizard_step()
    
    # Check that the state was updated but we're still at step 2
    assert state.get("resource_location") == "/path/to/docs"
    assert state.get_current_step() == 2
    
    # Simulate clicking the Next button for step 2
    clicked_buttons.add(f"Next_next_step_2")
    run_wizard_step()
    
    # Check that we moved to step 3
    assert state.get_current_step() == 3
    
    # Step 3: Set resource metadata
    mock_st.text_input.side_effect = ["Test User", "1.0", "test,documentation"]
    # Clear clicked buttons to ensure no automatic advancement
    clicked_buttons.clear()
    run_wizard_step()
    
    # Check that the state was updated
    assert state.get("resource_metadata") == {
        "author": "Test User",
        "version": "1.0",
        "tags": ["test", "documentation"]
    }
    
    # Reset the text_input mock to avoid StopIteration error
    # Use a simple return value instead of side_effect for the final step
    mock_st.text_input.side_effect = None
    mock_st.text_input.return_value = "Test Value"
    
    # Simulate clicking the Finish button
    clicked_buttons.add(f"Finish_finish_button")
    run_wizard_step()
    
    # Check that the wizard was completed
    assert state.is_completed() is True