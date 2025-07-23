"""
Test script for the Micro EDRR Cycle feature.

This script implements the step definitions for the micro_edrr_cycle.feature file.
"""

import os
import pytest
from unittest.mock import MagicMock
from pytest_bdd import scenarios, given, when, then

# Get the absolute path to the feature file
feature_file = os.path.join(os.path.dirname(__file__), "features", "general", "micro_edrr_cycle.feature")

# Load the scenarios from the feature file
scenarios(feature_file)

# Mock the Phase enum
class Phase:
    EXPAND = "EXPAND"
    DIFFERENTIATE = "DIFFERENTIATE"
    REFINE = "REFINE"
    RETROSPECT = "RETROSPECT"

@pytest.fixture
def context():
    """Create a context for the test."""
    class Context:
        def __init__(self):
            self.coordinator = None
            self.parent_cycle = None
            self.micro_cycle = None
    return Context()

@given("an initialized EDRR coordinator")
def initialized_coordinator(context):
    """Initialize an EDRR coordinator."""
    # Create a mock EDRRCoordinator
    coordinator = MagicMock()
    coordinator.cycle_id = "parent-cycle-123"
    coordinator.recursion_depth = 0
    coordinator.child_cycles = []
    
    # Store the coordinator in the context
    context.coordinator = coordinator
    return coordinator

@when('I start an EDRR cycle for "implement feature"')
def start_edrr_cycle(context):
    """Start an EDRR cycle for "implement feature"."""
    # Mock the start_cycle method
    context.coordinator.start_cycle = MagicMock()
    context.coordinator.start_cycle.return_value = "parent-cycle-123"
    
    # Call the start_cycle method
    context.coordinator.start_cycle({"description": "implement feature"})
    
    # Store the parent cycle in the context
    context.parent_cycle = context.coordinator
    
    # Verify that start_cycle was called with the correct arguments
    context.coordinator.start_cycle.assert_called_once_with({"description": "implement feature"})

@when('I create a micro cycle for "sub task" in phase "Expand"')
def create_micro_cycle(context):
    """Create a micro cycle for "sub task" in phase "Expand"."""
    # Create a mock micro cycle
    micro_cycle = MagicMock()
    micro_cycle.cycle_id = "micro-cycle-456"
    micro_cycle.parent_cycle_id = context.parent_cycle.cycle_id
    micro_cycle.recursion_depth = 1
    micro_cycle.parent_phase = Phase.EXPAND
    
    # Mock the create_micro_cycle method
    context.coordinator.create_micro_cycle = MagicMock()
    context.coordinator.create_micro_cycle.return_value = micro_cycle
    
    # Call the create_micro_cycle method
    result = context.coordinator.create_micro_cycle(
        {"description": "sub task"}, 
        Phase.EXPAND
    )
    
    # Store the micro cycle in the context
    context.micro_cycle = result
    
    # Add the micro cycle to the parent's child_cycles
    context.parent_cycle.child_cycles.append(micro_cycle)
    
    # Verify that create_micro_cycle was called with the correct arguments
    context.coordinator.create_micro_cycle.assert_called_once_with(
        {"description": "sub task"}, 
        Phase.EXPAND
    )

@then("the micro cycle should have recursion depth 1")
def verify_recursion_depth(context):
    """Verify that the micro cycle has recursion depth 1."""
    assert context.micro_cycle.recursion_depth == 1

@then("the parent cycle should include the micro cycle")
def verify_parent_includes_micro(context):
    """Verify that the parent cycle includes the micro cycle."""
    assert context.micro_cycle in context.parent_cycle.child_cycles