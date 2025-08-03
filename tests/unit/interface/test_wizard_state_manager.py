"""
Tests for the WizardStateManager class.

This module tests the methods in the WizardStateManager class, including
get_wizard_state, has_wizard_state, validate_wizard_state, reset_wizard_state,
and the navigation and data access methods.
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the fixtures
import sys
from pathlib import Path
fixtures_path = Path(__file__).parent.parent.parent / 'fixtures'
sys.path.insert(0, str(fixtures_path))
try:
    from state_access_fixture import ( mock_session_state, wizard_state_manager, gather_wizard_state_manager, simulate_wizard_manager_navigation, set_wizard_manager_data )
except ImportError:
    # For debugging import issues
    print(f"Fixtures path: {fixtures_path}")
    print(f"Fixtures path exists: {fixtures_path.exists()}")
    print(f"Files in fixtures directory: {list(fixtures_path.glob('*.py'))}")
    raise

# Import the class to test
from devsynth.interface.wizard_state_manager import WizardStateManager

@pytest.mark.medium

@pytest.fixture
def clean_state():
    """Set up clean state for tests."""
    # Store original session state keys to restore later
    original_keys = {}
    
    # Get all test wizard keys that might exist in session state
    wizard_keys = ["test_wizard", "gather_wizard"]
    
    # For each wizard, store and then clear its state
    for wizard_name in wizard_keys:
        prefix = f"{wizard_name}_"
        keys_to_store = [
            f"{prefix}current_step",
            f"{prefix}total_steps",
            f"{prefix}completed"
        ]
        
        # Add data keys based on wizard type
        if wizard_name == "test_wizard":
            for i in range(1, 4):
                keys_to_store.append(f"{prefix}step{i}_data")
        elif wizard_name == "gather_wizard":
            keys_to_store.extend([
                f"{prefix}resource_type",
                f"{prefix}resource_location",
                f"{prefix}resource_metadata"
            ])
        
        # Store original values
        from tests.fixtures.state_access_fixture import mock_session_state
        for key in keys_to_store:
            if key in mock_session_state:
                original_keys[key] = mock_session_state[key]
                del mock_session_state[key]
    
    yield
    
    # Clean up state after test
    # First clear any wizard state that might have been created during the test
    for wizard_name in wizard_keys:
        prefix = f"{wizard_name}_"
        keys_to_clear = []
        
        # Find all keys with this prefix
        for key in list(mock_session_state.keys()):
            if key.startswith(prefix):
                keys_to_clear.append(key)
        
        # Delete them
        for key in keys_to_clear:
            if key in mock_session_state:
                del mock_session_state[key]
    
    # Restore original values
    for key, value in original_keys.items():
        mock_session_state[key] = value

def test_wizard_state_manager_initialization(wizard_state_manager, clean_state):
    """Test that the wizard state manager is properly initialized."""
    manager, mock_session = wizard_state_manager
    
    # Check that the manager has the correct properties
    assert manager.wizard_name == "test_wizard"
    assert manager.steps == 3
    assert isinstance(manager.initial_state, dict)
    assert manager.initial_state == {
        "step1_data": "",
        "step2_data": "",
        "step3_data": ""
    }

@pytest.mark.medium

def test_get_wizard_state_new(mock_session_state, clean_state):
    """Test get_wizard_state when no wizard state exists."""
    # Create a manager with a clean session state
    manager = WizardStateManager(mock_session_state, "test_wizard", 3, { "step1_data": "", "step2_data": "", "step3_data": "" })
    
    # Mock the logger
    with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
        # Get the wizard state
        wizard_state = manager.get_wizard_state()
        
        # Check that the wizard state was created
        assert wizard_state is not None
        assert wizard_state.page_name == "test_wizard"
        assert wizard_state.get_total_steps() == 3
        assert wizard_state.get_current_step() == 1
        assert wizard_state.is_completed() is False
        
        # Check that the initial state was set
        assert wizard_state.get("step1_data") == ""
        assert wizard_state.get("step2_data") == ""
        assert wizard_state.get("step3_data") == ""
        
        # Check that the logger was called with the expected message
        mock_logger.debug.assert_called_once_with(f"Creating new WizardState for test_wizard")

@pytest.mark.medium

def test_get_wizard_state_existing(wizard_state_manager, clean_state):
    """Test get_wizard_state when a wizard state already exists."""
    manager, mock_session = wizard_state_manager
    
    # Set up the session state to simulate an existing wizard state
    mock_session["test_wizard_current_step"] = 2
    mock_session["test_wizard_total_steps"] = 3
    mock_session["test_wizard_completed"] = False
    mock_session["test_wizard_step1_data"] = "Step 1 Value"
    mock_session["test_wizard_step2_data"] = "Step 2 Value"
    mock_session["test_wizard_step3_data"] = "Step 3 Value"
    
    # Mock the logger
    with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
        # Get the wizard state
        wizard_state = manager.get_wizard_state()
        
        # Check that the wizard state was retrieved
        assert wizard_state is not None
        assert wizard_state.page_name == "test_wizard"
        assert wizard_state.get_total_steps() == 3
        assert wizard_state.get_current_step() == 2
        assert wizard_state.is_completed() is False
        
        # Check that the state values were preserved
        assert wizard_state.get("step1_data") == "Step 1 Value"
        assert wizard_state.get("step2_data") == "Step 2 Value"
        assert wizard_state.get("step3_data") == "Step 3 Value"
        
        # Check that the logger was called with the expected message
        mock_logger.debug.assert_called_once_with(f"Using existing WizardState for test_wizard")

@pytest.mark.medium

def test_has_wizard_state(wizard_state_manager, clean_state):
    """Test has_wizard_state method."""
    manager, mock_session = wizard_state_manager
    
    # Initially, there should be no wizard state
    assert manager.has_wizard_state() is False
    
    # Set up the session state to simulate an existing wizard state
    mock_session["test_wizard_current_step"] = 1
    
    # Now there should be a wizard state
    assert manager.has_wizard_state() is True

@pytest.mark.medium

def test_validate_wizard_state_valid(wizard_state_manager, clean_state):
    """Test validate_wizard_state with a valid state."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state
    wizard_state = manager.get_wizard_state()
    
    # Set some data
    wizard_state.set("step1_data", "Step 1 Value")
    wizard_state.set("step2_data", "Step 2 Value")
    wizard_state.set("step3_data", "Step 3 Value")
    
    # Validate the state
    assert manager.validate_wizard_state(wizard_state) is True

@pytest.mark.medium

def test_validate_wizard_state_missing_key(wizard_state_manager, clean_state):
    """Test validate_wizard_state with a missing key."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state
    wizard_state = manager.get_wizard_state()
    
    # Remove a key from the session state
    key = f"{wizard_state.page_name}_current_step"
    if key in mock_session:
        del mock_session[key]
    
    # Mock the logger
    with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
        # Validate the state
        assert manager.validate_wizard_state(wizard_state) is False
        
        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with( f"Missing expected key 'current_step' in wizard state for test_wizard" )

@pytest.mark.medium

def test_validate_wizard_state_invalid_step(wizard_state_manager, clean_state):
    """Test validate_wizard_state with an invalid step."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state
    wizard_state = manager.get_wizard_state()
    
    # Set an invalid current step
    mock_session[f"{wizard_state.page_name}_current_step"] = 10
    
    # Mock the logger
    with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
        # Validate the state
        assert manager.validate_wizard_state(wizard_state) is False
        
        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with( f"Invalid current_step value 10 for test_wizard (valid range: 1-3)"
)

@pytest.mark.medium

def test_validate_wizard_state_mismatched_steps(wizard_state_manager, clean_state):
    """Test validate_wizard_state with mismatched total steps."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state
    wizard_state = manager.get_wizard_state()
    
    # Set a mismatched total steps
    mock_session[f"{wizard_state.page_name}_total_steps"] = 5
    
    # Mock the logger
    with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
        # Validate the state
        assert manager.validate_wizard_state(wizard_state) is False
        
        # Check that the logger was called with the expected message
        mock_logger.warning.assert_called_once_with( f"Mismatched total_steps value 5 for test_wizard (expected: 3)"
)

@pytest.mark.medium

def test_reset_wizard_state(wizard_state_manager, clean_state):
    """Test reset_wizard_state method."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state and set some data
    wizard_state = manager.get_wizard_state()
    wizard_state.set("step1_data", "Step 1 Value")
    wizard_state.set("step2_data", "Step 2 Value")
    wizard_state.next_step()
    wizard_state.set_completed(True)
    
    # Reset the state
    with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
        result = manager.reset_wizard_state()
        
        # Check that the function returns True
        assert result is True
        
        # Check that the logger was called with the expected message
        mock_logger.debug.assert_called_once_with(f"Reset wizard state for test_wizard")
    
    # Get a fresh wizard state
    wizard_state = manager.get_wizard_state()
    
    # Check that everything is back to initial values
    assert wizard_state.get_current_step() == 1
    assert wizard_state.is_completed() is False
    assert wizard_state.get("step1_data") == ""
    assert wizard_state.get("step2_data") == ""
    assert wizard_state.get("step3_data") == ""

@pytest.mark.medium

def test_reset_wizard_state_error(wizard_state_manager, clean_state):
    """Test reset_wizard_state method with an error."""
    manager, mock_session = wizard_state_manager
    
    # Mock the WizardState.reset method to raise an exception
    with patch('devsynth.interface.webui_state.WizardState.reset', side_effect=Exception("Test error")):
        # Mock the logger
        with patch('devsynth.interface.wizard_state_manager.logger') as mock_logger:
            # Reset the state
            result = manager.reset_wizard_state()
            
            # Check that the function returns False
            assert result is False
            
            # Check that the logger was called with the expected message
            mock_logger.error.assert_called_once_with( f"Error resetting wizard state for test_wizard: Test error" )

@pytest.mark.medium

def test_get_current_step(wizard_state_manager, clean_state):
    """Test get_current_step method."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state and set the current step
    wizard_state = manager.get_wizard_state()
    wizard_state.go_to_step(2)
    
    # Get the current step
    assert manager.get_current_step() == 2

@pytest.mark.medium
def test_go_to_step(wizard_state_manager, clean_state):
    """Test go_to_step method."""
    manager, mock_session = wizard_state_manager
    
    # Go to step 2
    with patch('devsynth.interface.webui_state.WizardState.go_to_step', return_value=True) as mock_go_to_step:
        result = manager.go_to_step(2)
        
        # Check that the function returns True
        assert result is True
        
        # Check that the WizardState.go_to_step method was called with the expected arguments
        mock_go_to_step.assert_called_once_with(2)

@pytest.mark.medium

def test_next_step(wizard_state_manager, clean_state):
    """Test next_step method."""
    manager, mock_session = wizard_state_manager
    
    # Move to the next step
    with patch('devsynth.interface.webui_state.WizardState.next_step', return_value=True) as mock_next_step:
        result = manager.next_step()
        
        # Check that the function returns True
        assert result is True
        
        # Check that the WizardState.next_step method was called
        mock_next_step.assert_called_once()

@pytest.mark.medium

def test_previous_step(wizard_state_manager, clean_state):
    """Test previous_step method."""
    manager, mock_session = wizard_state_manager
    
    # Move to the previous step
    with patch('devsynth.interface.webui_state.WizardState.previous_step', return_value=True) as mock_previous_step:
        result = manager.previous_step()
        
        # Check that the function returns True
        assert result is True
        
        # Check that the WizardState.previous_step method was called
        mock_previous_step.assert_called_once()

@pytest.mark.medium

def test_set_completed(wizard_state_manager, clean_state):
    """Test set_completed method."""
    manager, mock_session = wizard_state_manager
    
    # Set the wizard as completed
    with patch('devsynth.interface.webui_state.WizardState.set_completed', return_value=True) as mock_set_completed:
        result = manager.set_completed(True)
        
        # Check that the function returns True
        assert result is True
        
        # Check that the WizardState.set_completed method was called with the expected arguments
        mock_set_completed.assert_called_once_with(True)

@pytest.mark.medium

def test_is_completed(wizard_state_manager, clean_state):
    """Test is_completed method."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state and set it as completed
    wizard_state = manager.get_wizard_state()
    wizard_state.set_completed(True)
    
    # Check if the wizard is completed
    assert manager.is_completed() is True

@pytest.mark.medium
def test_get_value(wizard_state_manager, clean_state):
    """Test get_value method."""
    manager, mock_session = wizard_state_manager
    
    # Get a wizard state and set a value
    wizard_state = manager.get_wizard_state()
    wizard_state.set("step1_data", "Step 1 Value")
    
    # Get the value
    assert manager.get_value("step1_data") == "Step 1 Value"
    assert manager.get_value("missing_key", "default") == "default"

@pytest.mark.medium

def test_set_value(wizard_state_manager, clean_state):
    """Test set_value method."""
    manager, mock_session = wizard_state_manager
    
    # Set a value
    with patch('devsynth.interface.webui_state.WizardState.set', return_value=True) as mock_set:
        result = manager.set_value("step1_data", "Step 1 Value")
        
        # Check that the function returns True
        assert result is True
        
        # Check that the WizardState.set method was called with the expected arguments
        mock_set.assert_called_once_with("step1_data", "Step 1 Value")

@pytest.mark.medium

def test_simulate_wizard_manager_navigation(wizard_state_manager, clean_state):
    """Test the simulate_wizard_manager_navigation helper function."""
    manager, mock_session = wizard_state_manager
    
    # Define a navigation sequence
    navigation_steps = ['next', 'next', 'previous', 'next', 'goto_1', 'next']
    
    # Simulate the navigation
    final_step = simulate_wizard_manager_navigation(manager, navigation_steps)
    
    # Check the final step
    assert final_step == 2
    assert manager.get_current_step() == 2

@pytest.mark.medium

def test_set_wizard_manager_data(wizard_state_manager, clean_state):
    """Test the set_wizard_manager_data helper function."""
    manager, mock_session = wizard_state_manager
    
    # Define data for multiple steps
    step_data = {
        "step1_data": "Step 1 Value",
        "step2_data": "Step 2 Value",
        "step3_data": "Step 3 Value"
    }
    
    # Set the data
    set_wizard_manager_data(manager, step_data)
    
    # Check that all data was set
    assert manager.get_value("step1_data") == "Step 1 Value"
    assert manager.get_value("step2_data") == "Step 2 Value"
    assert manager.get_value("step3_data") == "Step 3 Value"

@pytest.mark.medium

def test_gather_wizard_state_manager(gather_wizard_state_manager, clean_state):
    """Test the gather_wizard_state_manager fixture."""
    manager, mock_session = gather_wizard_state_manager
    
    # Check that the manager has the correct properties
    assert manager.wizard_name == "gather_wizard"
    assert manager.steps == 3
    assert isinstance(manager.initial_state, dict)
    assert manager.initial_state == {
        "resource_type": "",
        "resource_location": "",
        "resource_metadata": {}
    }
    
    # Get the wizard state
    wizard_state = manager.get_wizard_state()
    
    # Check that the wizard state has the correct properties
    assert wizard_state.page_name == "gather_wizard"
    assert wizard_state.get_total_steps() == 3
    assert wizard_state.get_current_step() == 1
    assert wizard_state.is_completed() is False
    
    # Check that the initial state was set
    assert wizard_state.get("resource_type") == ""
    assert wizard_state.get("resource_location") == ""
    assert isinstance(wizard_state.get("resource_metadata"), dict)

@pytest.mark.medium

def test_gather_wizard_workflow(gather_wizard_state_manager, clean_state):
    """Test a complete gather wizard workflow with state persistence."""
    manager, mock_session = gather_wizard_state_manager
    
    # Step 1: Set resource type
    assert manager.get_current_step() == 1
    manager.set_value("resource_type", "documentation")
    
    # Move to step 2
    manager.next_step()
    assert manager.get_current_step() == 2
    
    # Step 2: Set resource location
    manager.set_value("resource_location", "/path/to/docs")
    
    # Move to step 3
    manager.next_step()
    assert manager.get_current_step() == 3
    
    # Step 3: Set resource metadata
    metadata = {
        "author": "Test User",
        "version": "1.0",
        "tags": ["test", "documentation"]
    }
    manager.set_value("resource_metadata", metadata)
    
    # Complete the wizard
    manager.set_completed(True)
    
    # Check that all data is still there
    assert manager.get_value("resource_type") == "documentation"
    assert manager.get_value("resource_location") == "/path/to/docs"
    assert manager.get_value("resource_metadata") == metadata
    assert manager.is_completed() is True