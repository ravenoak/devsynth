from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file


scenarios(feature_path(__file__, "general", "micro_edrr_cycle.feature"))

import json

# Import the necessary components
import os
import tempfile
from pathlib import Path
from typing import Dict, Tuple
from unittest.mock import MagicMock

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryItem
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def context():
    """Fixture that provides a context object for the tests."""

    class Context:
        def __init__(self):
            """Initialize the context with empty attributes."""
            self.edrr_coordinator = None
            self.memory_manager = None
            self.memory_adapter = None
            self.wsde_team = None
            self.code_analyzer = None
            self.ast_transformer = None
            self.prompt_manager = None
            self.documentation_manager = None
            self.cycle_id = None
            self.micro_cycle = None
            self.parent_cycle = None
            self.task_description = None
            self.sub_task_description = None
            self.phase = None
            self.start_called = False
            self.end_called = False

    return Context()


@given("an initialized EDRR coordinator")
def edrr_coordinator_initialized(context):
    """
    Initialize the EDRR coordinator with all required components.

    This step creates all the necessary dependencies for the EDRR coordinator:
    - Memory manager for storing and retrieving data
    - WSDE team for collaborative problem solving
    - Code analyzer and AST transformer for code analysis
    - Prompt manager for managing prompts
    - Documentation manager for retrieving documentation

    The EDRR coordinator is initialized with enhanced logging enabled to provide
    detailed information about the execution of the EDRR cycle.

    Args:
        context: The test context object that holds the state between steps
    """
    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()

    # Initialize an in-memory adapter to avoid external dependencies
    class InMemoryAdapter:
        def __init__(self):
            self.items = []

        def store(self, item: MemoryItem) -> str:
            item.id = str(len(self.items) + 1)
            self.items.append(item)
            return item.id

        def query_by_metadata(self, metadata):
            return [
                item
                for item in self.items
                if all(item.metadata.get(k) == v for k, v in metadata.items())
            ]

    context.memory_adapter = InMemoryAdapter()
    context.memory_manager = MemoryManager(
        adapters={"in_memory": context.memory_adapter}
    )

    # Initialize WSDE team (mock)
    context.wsde_team = MagicMock()
    context.wsde_team.generate_diverse_ideas.return_value = []
    assert context.wsde_team is not None, "WSDE team initialization failed"

    # Initialize code analyzer and AST transformer
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    assert context.code_analyzer is not None, "Code analyzer initialization failed"
    assert context.ast_transformer is not None, "AST transformer initialization failed"

    # Initialize prompt manager
    context.prompt_manager = PromptManager()
    assert context.prompt_manager is not None, "Prompt manager initialization failed"

    # Initialize documentation manager
    context.documentation_manager = DocumentationManager(context.memory_manager)
    assert (
        context.documentation_manager is not None
    ), "Documentation manager initialization failed"

    # Initialize EDRR coordinator
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager,
        enable_enhanced_logging=True,
    )
    assert (
        context.edrr_coordinator is not None
    ), "EDRR coordinator initialization failed"

    # Store the parent cycle for later reference
    context.parent_cycle = context.edrr_coordinator


@given("I register micro cycle monitoring hooks")
def register_micro_cycle_hooks(context):
    """Register hooks that toggle flags in the context when invoked."""

    def start_hook(info):
        context.start_called = True

    def end_hook(info):
        context.end_called = True

    context.edrr_coordinator.register_micro_cycle_hook("start", start_hook)
    context.edrr_coordinator.register_micro_cycle_hook("end", end_hook)


@when(parsers.parse('I start an EDRR cycle for "{task_description}"'))
def start_edrr_cycle(context, task_description):
    """
    Start an EDRR cycle with the given task description.

    This step initiates a new EDRR cycle with the specified task description.
    The task description is stored in the context for later reference, and
    the cycle ID is captured for verification.

    Args:
        context: The test context object that holds the state between steps
        task_description: The description of the task to be performed in the EDRR cycle
    """
    context.task_description = task_description

    # Start the EDRR cycle
    context.edrr_coordinator.start_cycle({"description": task_description})

    # Capture the cycle ID for later verification
    context.cycle_id = context.edrr_coordinator.cycle_id

    # Verify that the cycle was started successfully
    assert context.cycle_id is not None, "EDRR cycle ID should not be None"
    assert (
        context.edrr_coordinator.current_phase is not None
    ), "EDRR cycle should have a current phase"
    assert (
        context.edrr_coordinator.results is not None
    ), "EDRR cycle should have results dictionary initialized"


@when(
    parsers.parse(
        'I create a micro cycle for "{sub_task_description}" in phase "{phase_name}"'
    )
)
def create_micro_cycle(context, sub_task_description, phase_name):
    """
    Create a micro cycle for the given sub-task in the specified phase.

    This step creates a micro EDRR cycle within the parent cycle for the specified sub-task.
    The micro cycle is created in the specified phase of the parent cycle.
    If the parent cycle is not already in the specified phase, it is progressed to that phase.

    Args:
        context: The test context object that holds the state between steps
        sub_task_description: The description of the sub-task to be performed in the micro cycle
        phase_name: The name of the phase in which to create the micro cycle (e.g., "Expand")
    """
    # Store the sub-task description and phase for later reference
    context.sub_task_description = sub_task_description
    context.phase = Phase[phase_name.upper()]

    # Ensure we're in the correct phase
    if context.edrr_coordinator.current_phase != context.phase:
        context.edrr_coordinator.progress_to_phase(context.phase)

    # Verify that we're in the correct phase
    assert (
        context.edrr_coordinator.current_phase == context.phase
    ), f"Expected to be in phase {context.phase}, but current phase is {context.edrr_coordinator.current_phase}"

    # Create the micro cycle
    context.micro_cycle = context.edrr_coordinator.create_micro_cycle(
        {"description": sub_task_description}, context.phase
    )

    # Verify that the micro cycle was created successfully
    assert context.micro_cycle is not None, "Micro cycle should not be None"
    assert context.micro_cycle.cycle_id is not None, "Micro cycle ID should not be None"
    assert (
        context.micro_cycle.parent_cycle_id == context.edrr_coordinator.cycle_id
    ), "Micro cycle should have the parent cycle ID as its parent_cycle_id"


@then(parsers.parse("the micro cycle should have recursion depth {depth:d}"))
def verify_recursion_depth(context, depth):
    """
    Verify that the micro cycle has the expected recursion depth.

    This step verifies that the micro cycle has the expected recursion depth.
    The recursion depth is a property of the EDRRCoordinator that indicates
    how many levels deep the cycle is in the recursion hierarchy.

    Args:
        context: The test context object that holds the state between steps
        depth: The expected recursion depth of the micro cycle
    """
    # Verify that the micro cycle exists
    assert context.micro_cycle is not None, "Micro cycle was not created"

    # Verify that the micro cycle has the expected recursion depth
    assert (
        context.micro_cycle.recursion_depth == depth
    ), f"Expected recursion depth {depth}, but got {context.micro_cycle.recursion_depth}"

    # Verify that the recursion depth is greater than the parent cycle's recursion depth
    assert (
        context.micro_cycle.recursion_depth > context.parent_cycle.recursion_depth
    ), "Micro cycle recursion depth should be greater than parent cycle recursion depth"


@then("the parent cycle should include the micro cycle")
def verify_parent_includes_micro(context):
    """
    Verify that the parent cycle includes the micro cycle.

    This step verifies that the parent cycle includes the micro cycle in its child_cycles list,
    and that the micro cycle is properly stored in the parent cycle's results.
    It also verifies that the micro cycle task is stored correctly with the expected description.

    The parent-child relationship between EDRR cycles is important for the recursion feature,
    as it allows the parent cycle to aggregate results from its child cycles.

    Args:
        context: The test context object that holds the state between steps
    """
    # Verify that the micro cycle exists
    assert context.micro_cycle is not None, "Micro cycle was not created"

    # Verify that the micro cycle is in the parent cycle's child_cycles list
    assert context.micro_cycle.cycle_id in [
        cycle.cycle_id for cycle in context.parent_cycle.child_cycles
    ], "Parent cycle does not include the micro cycle in its child_cycles list"

    # Verify that the micro cycle is stored in the parent's results
    phase_key = context.phase.name
    assert (
        phase_key in context.parent_cycle.results
    ), f"Phase {phase_key} not found in parent cycle results"
    assert (
        "micro_cycle_results" in context.parent_cycle.results[phase_key]
    ), "micro_cycle_results not found in parent cycle phase results"
    assert (
        context.micro_cycle.cycle_id
        in context.parent_cycle.results[phase_key]["micro_cycle_results"]
    ), "Micro cycle ID not found in parent cycle micro_cycle_results"

    # Verify that the micro cycle task is stored correctly
    assert (
        "task"
        in context.parent_cycle.results[phase_key]["micro_cycle_results"][
            context.micro_cycle.cycle_id
        ]
    ), "Task not found in micro cycle results"
    assert (
        context.parent_cycle.results[phase_key]["micro_cycle_results"][
            context.micro_cycle.cycle_id
        ]["task"]["description"]
        == context.sub_task_description
    ), "Micro cycle task description does not match"

    # Verify that the parent cycle has a reference to the micro cycle's memory items
    # This is important for result aggregation
    memory_items = context.memory_manager.query_by_metadata(
        {"cycle_id": context.micro_cycle.cycle_id}
    )
    assert len(memory_items) > 0, "Micro cycle should have memory items"


@then("the hooks should record the micro cycle lifecycle")
def hooks_recorded(context):
    """Ensure start and end hooks were triggered."""
    assert context.start_called is True
    assert context.end_called is True
