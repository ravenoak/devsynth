"""Step definitions for the Recursive EDRR Coordinator feature."""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file


scenarios(feature_path(__file__, "general", "recursive_edrr_coordinator.feature"))

# Import the necessary components

import json
import os
import tempfile
from pathlib import Path

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.edrr.manifest_parser import ManifestParser
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def context():
    """Fixture to provide a context object for storing test state between steps."""

    class Context:
        def __init__(self):
            self.memory_manager = None
            self.wsde_team = None
            self.code_analyzer = None
            self.ast_transformer = None
            self.prompt_manager = None
            self.documentation_manager = None
            self.edrr_coordinator = None
            self.task = None
            self.micro_cycles = {}
            self.current_micro_cycle = None
            self.exception = None

    return Context()


@given("the EDRR coordinator is initialized with recursion support")
def edrr_coordinator_initialized_with_recursion(context):
    """Initialize the EDRR coordinator with recursion support."""
    # Initialize memory adapter
    from devsynth.application.memory.adapters.tinydb_memory_adapter import (
        TinyDBMemoryAdapter,
    )

    memory_adapter = TinyDBMemoryAdapter()  # Use in-memory database for testing

    # Initialize actual dependencies
    context.memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    context.wsde_team = WSDETeam(name="RecursiveEDRRTeam")
    context.code_analyzer = CodeAnalyzer()
    context.ast_transformer = AstTransformer()
    context.prompt_manager = PromptManager(storage_path="tests/fixtures/prompts")
    context.documentation_manager = DocumentationManager(
        memory_manager=context.memory_manager, storage_path="tests/fixtures/docs"
    )

    # Initialize the EDRRCoordinator with recursion support
    context.edrr_coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=context.code_analyzer,
        ast_transformer=context.ast_transformer,
        prompt_manager=context.prompt_manager,
        documentation_manager=context.documentation_manager,
        enable_enhanced_logging=True,
    )

    # Verify recursion support attributes
    assert hasattr(context.edrr_coordinator, "parent_cycle_id")
    assert hasattr(context.edrr_coordinator, "recursion_depth")
    assert hasattr(context.edrr_coordinator, "child_cycles")
    assert hasattr(context.edrr_coordinator, "max_recursion_depth")
    assert hasattr(context.edrr_coordinator, "should_terminate_recursion")
    assert hasattr(context.edrr_coordinator, "create_micro_cycle")


@given("the memory system is available")
def memory_system_available(context):
    """Make the memory system available."""
    # The memory manager is already initialized in edrr_coordinator_initialized
    assert context.memory_manager is not None
    assert context.edrr_coordinator.memory_manager is context.memory_manager


@given("the WSDE team is available")
def wsde_team_available(context):
    """Make the WSDE team available."""
    # The WSDE team is already initialized in edrr_coordinator_initialized
    assert context.wsde_team is not None
    assert context.edrr_coordinator.wsde_team is context.wsde_team


@given("the AST analyzer is available")
def ast_analyzer_available(context):
    """Make the AST analyzer available."""
    # The AST analyzer is already initialized in edrr_coordinator_initialized
    assert context.code_analyzer is not None
    assert context.ast_transformer is not None
    assert context.edrr_coordinator.code_analyzer is context.code_analyzer
    assert context.edrr_coordinator.ast_transformer is context.ast_transformer


@given("the prompt manager is available")
def prompt_manager_available(context):
    """Make the prompt manager available."""
    # The prompt manager is already initialized in edrr_coordinator_initialized
    assert context.prompt_manager is not None
    assert context.edrr_coordinator.prompt_manager is context.prompt_manager


@given("the documentation manager is available")
def documentation_manager_available(context):
    """Make the documentation manager available."""
    # The documentation manager is already initialized in edrr_coordinator_initialized
    assert context.documentation_manager is not None
    assert (
        context.edrr_coordinator.documentation_manager is context.documentation_manager
    )


@when(parsers.parse('I start the EDRR cycle with a task to "{task_description}"'))
def start_edrr_cycle(context, task_description):
    """Start the EDRR cycle with a task."""
    context.task = {"id": "task-123", "description": task_description}
    context.edrr_coordinator.start_cycle(context.task)


@given(parsers.parse('the "{phase_name}" phase has completed for a task'))
def phase_completed(context, phase_name):
    """Set up a completed phase."""
    # Start a new cycle with a task
    context.task = {"id": "task-123", "description": "implement a feature"}
    context.edrr_coordinator.start_cycle(context.task)

    # Set up the phase
    phase = Phase[phase_name.upper()]

    # Set up necessary data for each phase
    if (
        phase == Phase.EXPAND
        or phase == Phase.DIFFERENTIATE
        or phase == Phase.REFINE
        or phase == Phase.RETROSPECT
    ):
        # Set up data for EXPAND phase
        context.edrr_coordinator.results[Phase.EXPAND] = {
            "completed": True,
            "approaches": [
                {
                    "id": "approach-1",
                    "description": "First approach",
                    "code": "def approach1(): pass",
                },
                {
                    "id": "approach-2",
                    "description": "Second approach",
                    "code": "def approach2(): pass",
                },
            ],
        }
        context.edrr_coordinator.progress_to_phase(Phase.EXPAND)

    if (
        phase == Phase.DIFFERENTIATE
        or phase == Phase.REFINE
        or phase == Phase.RETROSPECT
    ):
        # Set up data for DIFFERENTIATE phase
        context.edrr_coordinator.results[Phase.DIFFERENTIATE] = {
            "completed": True,
            "evaluation": {
                "selected_approach": {
                    "id": "approach-1",
                    "description": "Selected approach",
                    "code": "def example(): pass",
                }
            },
        }
        context.edrr_coordinator.progress_to_phase(Phase.DIFFERENTIATE)

    if phase == Phase.REFINE or phase == Phase.RETROSPECT:
        # Set up data for REFINE phase
        context.edrr_coordinator.results[Phase.REFINE] = {
            "completed": True,
            "implementation": {
                "code": "def example(): return 'Hello, World!'",
                "description": "Implemented solution",
            },
        }
        context.edrr_coordinator.progress_to_phase(Phase.REFINE)

    if phase == Phase.RETROSPECT:
        # Progress to RETROSPECT phase
        context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)

    # Ensure the phase is marked as completed
    if (
        phase not in context.edrr_coordinator.results
        or not context.edrr_coordinator.results[phase].get("completed", False)
    ):
        context.edrr_coordinator.results[phase] = {
            "completed": True,
            "outputs": [{"type": "approach", "content": "Sample approach"}],
        }


@when(parsers.parse('the coordinator progresses to the "{phase_name}" phase'))
def progress_to_phase(context, phase_name):
    """Progress to the next phase."""
    context.edrr_coordinator.progress_to_phase(Phase[phase_name.upper()])


@then(parsers.parse('the coordinator should enter the "{phase_name}" phase'))
def verify_phase(context, phase_name):
    """Verify the coordinator has entered the specified phase."""
    assert context.edrr_coordinator.current_phase == Phase[phase_name.upper()]


@when(
    parsers.parse(
        'I create a micro-EDRR cycle for "{task_description}" within the "{phase_name}" phase'
    )
)
def create_micro_cycle(context, task_description, phase_name):
    """Create a micro-EDRR cycle within the specified phase."""
    micro_task = {"description": task_description}
    phase = Phase[phase_name.upper()]

    # Create the micro cycle
    micro_cycle = context.edrr_coordinator.create_micro_cycle(micro_task, phase)

    # Store the micro cycle in the context
    context.micro_cycles[task_description] = micro_cycle
    context.current_micro_cycle = micro_cycle


@when(
    parsers.parse(
        'I create a micro-EDRR cycle for "{task_description}" within the "{phase_name}" phase of the "{parent_task}" cycle'
    )
)
def create_nested_micro_cycle(context, task_description, phase_name, parent_task):
    """Create a nested micro-EDRR cycle within the specified phase of a parent micro cycle."""
    micro_task = {"description": task_description}
    phase = Phase[phase_name.upper()]

    # Get the parent micro cycle
    parent_cycle = context.micro_cycles[parent_task]

    # Create the micro cycle
    micro_cycle = parent_cycle.create_micro_cycle(micro_task, phase)

    # Store the micro cycle in the context
    context.micro_cycles[task_description] = micro_cycle
    context.current_micro_cycle = micro_cycle


@then("the micro cycle should be created successfully")
def verify_micro_cycle_created(context):
    """Verify the micro cycle was created successfully."""
    assert context.current_micro_cycle is not None
    assert isinstance(context.current_micro_cycle, EDRRCoordinator)


@then("the micro cycle should have the parent cycle ID set correctly")
def verify_parent_cycle_id(context):
    """Verify the micro cycle has the correct parent cycle ID."""
    assert (
        context.current_micro_cycle.parent_cycle_id == context.edrr_coordinator.cycle_id
    )


@then("the micro cycle should have recursion depth of 1")
def verify_recursion_depth(context):
    """Verify the micro cycle has recursion depth of 1."""
    assert context.current_micro_cycle.recursion_depth == 1


@then("the micro cycle should be tracked as a child of the parent cycle")
def verify_child_tracking(context):
    """Verify the micro cycle is tracked as a child of the parent cycle."""
    assert context.current_micro_cycle in context.edrr_coordinator.child_cycles


@when(parsers.parse('the micro cycle executes its "{phase_name}" phase'))
def execute_micro_cycle_phase(context, phase_name):
    """Execute the specified phase of the micro cycle."""
    # Ensure the micro cycle is in the correct phase
    if context.current_micro_cycle.current_phase != Phase[phase_name.upper()]:
        context.current_micro_cycle.progress_to_phase(Phase[phase_name.upper()])

    # Execute the phase
    context.current_micro_cycle.execute_current_phase()


@when('the micro cycle progresses to the "Differentiate" phase')
def progress_micro_cycle_to_differentiate(context):
    """Progress the micro cycle to the Differentiate phase."""
    context.current_micro_cycle.progress_to_phase(Phase.DIFFERENTIATE)


@when("the micro cycle completes a full EDRR cycle")
def complete_micro_cycle(context):
    """Complete a full EDRR cycle for the micro cycle."""
    # Execute each phase
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        # Ensure the micro cycle is in the correct phase
        if context.current_micro_cycle.current_phase != phase:
            context.current_micro_cycle.progress_to_phase(phase)

        # Execute the phase
        context.current_micro_cycle.execute_current_phase()


@then(parsers.parse('the micro cycle should generate ideas for "{task_description}"'))
def verify_micro_cycle_ideas(context, task_description):
    """Verify the micro cycle generates ideas for the specified task."""
    # Check that the micro cycle has results for the Expand phase
    phase_key = Phase.EXPAND.name
    assert (
        phase_key in context.current_micro_cycle.results
    ), f"Phase key '{phase_key}' not in results: {list(context.current_micro_cycle.results.keys())}"
    assert (
        "ideas" in context.current_micro_cycle.results[phase_key]
    ), f"'ideas' not in results[{phase_key}]: {list(context.current_micro_cycle.results[phase_key].keys())}"
    assert len(context.current_micro_cycle.results[phase_key]["ideas"]) > 0


@then(parsers.parse('the micro cycle should evaluate options for "{task_description}"'))
def verify_micro_cycle_evaluation(context, task_description):
    """Verify the micro cycle evaluates options for the specified task."""
    # Check that the micro cycle has results for the Differentiate phase
    phase_key = Phase.DIFFERENTIATE.name
    assert (
        phase_key in context.current_micro_cycle.results
    ), f"Phase key '{phase_key}' not in results: {list(context.current_micro_cycle.results.keys())}"
    assert (
        "evaluated_options" in context.current_micro_cycle.results[phase_key]
    ), f"'evaluated_options' not in results[{phase_key}]: {list(context.current_micro_cycle.results[phase_key].keys())}"
    assert len(context.current_micro_cycle.results[phase_key]["evaluated_options"]) > 0


@then(
    parsers.parse(
        'the micro cycle should produce an implementation for "{task_description}"'
    )
)
def verify_micro_cycle_implementation(context, task_description):
    """Verify the micro cycle produces an implementation for the specified task."""
    # Check that the micro cycle has results for the Refine phase
    phase_key = Phase.REFINE.name
    assert (
        phase_key in context.current_micro_cycle.results
    ), f"Phase key '{phase_key}' not in results: {list(context.current_micro_cycle.results.keys())}"

    # Check for either 'implementation' or other implementation-related keys
    refine_results = context.current_micro_cycle.results[phase_key]
    implementation_keys = [
        "implementation",
        "selected_option",
        "detailed_plan",
        "optimized_implementation",
    ]

    # Check if at least one of the implementation keys exists
    has_implementation = any(key in refine_results for key in implementation_keys)
    assert (
        has_implementation
    ), f"No implementation-related keys found in results[{phase_key}]: {list(refine_results.keys())}"

    # Verify that the implementation data is not empty
    for key in implementation_keys:
        if key in refine_results and refine_results[key] is not None:
            return

    # If we get here, none of the implementation keys had valid data
    assert False, f"No valid implementation data found in results[{phase_key}]"


@then(
    parsers.parse('the micro cycle should produce learnings for "{task_description}"')
)
def verify_micro_cycle_learnings(context, task_description):
    """Verify the micro cycle produces learnings for the specified task."""
    # Check that the micro cycle has results for the Retrospect phase
    phase_key = Phase.RETROSPECT.name
    assert (
        phase_key in context.current_micro_cycle.results
    ), f"Phase key '{phase_key}' not in results: {list(context.current_micro_cycle.results.keys())}"
    assert (
        "learnings" in context.current_micro_cycle.results[phase_key]
    ), f"'learnings' not in results[{phase_key}]: {list(context.current_micro_cycle.results[phase_key].keys())}"
    assert len(context.current_micro_cycle.results[phase_key]["learnings"]) > 0


@then("the micro cycle results should be integrated into the parent cycle")
def verify_results_integration(context):
    """Verify the micro cycle results are integrated into the parent cycle."""
    # Check that the parent cycle has the micro cycle results
    parent_phase = context.current_micro_cycle.parent_phase
    phase_key = parent_phase.name if parent_phase else None

    # Ensure the phase key exists in the results
    assert phase_key is not None, "Parent phase is None"
    assert (
        phase_key in context.edrr_coordinator.results
    ), f"Phase key '{phase_key}' not in results: {list(context.edrr_coordinator.results.keys())}"

    # The integration mechanism will depend on the specific implementation
    # For now, we'll check that there's a "micro_cycle_results" key in the parent phase results
    assert (
        "micro_cycle_results" in context.edrr_coordinator.results[phase_key]
    ), f"'micro_cycle_results' not in results[{phase_key}]: {list(context.edrr_coordinator.results[phase_key].keys())}"
    assert (
        context.current_micro_cycle.cycle_id
        in context.edrr_coordinator.results[phase_key]["micro_cycle_results"]
    ), f"Cycle ID {context.current_micro_cycle.cycle_id} not in micro_cycle_results: {list(context.edrr_coordinator.results[phase_key]['micro_cycle_results'].keys())}"


@then(
    "attempting to create another micro cycle should fail due to recursion depth limits"
)
def verify_recursion_depth_limit(context):
    """Verify that attempting to create a micro cycle beyond the recursion depth limit fails."""
    # Attempt to create a micro cycle beyond the recursion depth limit
    try:
        context.exception = None
        level_3_cycle = context.micro_cycles["level 3 task"]
        level_4_task = {"description": "level 4 task"}
        level_3_cycle.create_micro_cycle(level_4_task, Phase.EXPAND)
    except EDRRCoordinatorError as e:
        context.exception = e

    # Verify that an exception was raised
    assert context.exception is not None
    assert "recursion depth" in str(context.exception).lower()


@then("creating a micro cycle for a very granular task should be prevented")
def verify_granularity_threshold(context):
    """Verify that creating a micro cycle for a very granular task is prevented."""
    # Create a very granular task
    granular_task = {"description": "Very small task", "granularity_score": 0.1}

    # Attempt to create a micro cycle
    try:
        context.exception = None
        context.edrr_coordinator.create_micro_cycle(granular_task, Phase.EXPAND)
    except EDRRCoordinatorError as e:
        context.exception = e

    # Verify that an exception was raised
    assert context.exception is not None
    assert "granularity" in str(context.exception).lower()


@then("creating a micro cycle for a complex task should be allowed")
def verify_complex_task_allowed(context):
    """Verify that creating a micro cycle for a complex task is allowed."""
    # Create a complex task
    complex_task = {"description": "Complex task", "granularity_score": 0.8}

    # Attempt to create a micro cycle
    try:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(
            complex_task, Phase.EXPAND
        )
        assert micro_cycle is not None
    except Exception as e:
        pytest.fail(
            f"Creating a micro cycle for a complex task raised an exception: {e}"
        )


@then("creating a micro cycle for a high-cost low-benefit task should be prevented")
def verify_cost_benefit_analysis(context):
    """Verify that creating a micro cycle for a high-cost low-benefit task is prevented."""
    # Create a high-cost low-benefit task
    costly_task = {
        "description": "High cost task",
        "cost_score": 0.9,
        "benefit_score": 0.2,
    }

    # Attempt to create a micro cycle
    try:
        context.exception = None
        context.edrr_coordinator.create_micro_cycle(costly_task, Phase.EXPAND)
    except EDRRCoordinatorError as e:
        context.exception = e

    # Verify that an exception was raised
    assert context.exception is not None
    assert "cost-benefit" in str(context.exception).lower()


@then("creating a micro cycle for a low-cost high-benefit task should be allowed")
def verify_beneficial_task_allowed(context):
    """Verify that creating a micro cycle for a low-cost high-benefit task is allowed."""
    # Create a low-cost high-benefit task
    beneficial_task = {
        "description": "High benefit task",
        "cost_score": 0.3,
        "benefit_score": 0.8,
    }

    # Attempt to create a micro cycle
    try:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(
            beneficial_task, Phase.EXPAND
        )
        assert micro_cycle is not None
    except Exception as e:
        pytest.fail(
            f"Creating a micro cycle for a beneficial task raised an exception: {e}"
        )


@then(
    "creating a micro cycle for a task that already meets quality thresholds should be prevented"
)
def verify_quality_threshold(context):
    """Verify that creating a micro cycle for a task that already meets quality thresholds is prevented."""
    # Create a high-quality task
    high_quality_task = {"description": "High quality task", "quality_score": 0.95}

    # Attempt to create a micro cycle
    try:
        context.exception = None
        context.edrr_coordinator.create_micro_cycle(high_quality_task, Phase.EXPAND)
    except EDRRCoordinatorError as e:
        context.exception = e

    # Verify that an exception was raised
    assert context.exception is not None
    assert "quality" in str(context.exception).lower()


@then(
    "creating a micro cycle for a task that needs quality improvement should be allowed"
)
def verify_low_quality_task_allowed(context):
    """Verify that creating a micro cycle for a task that needs quality improvement is allowed."""
    # Create a low-quality task
    low_quality_task = {"description": "Low quality task", "quality_score": 0.5}

    # Attempt to create a micro cycle
    try:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(
            low_quality_task, Phase.EXPAND
        )
        assert micro_cycle is not None
    except Exception as e:
        pytest.fail(
            f"Creating a micro cycle for a low quality task raised an exception: {e}"
        )


@then("creating a micro cycle for a resource-intensive task should be prevented")
def verify_resource_limits(context):
    """Verify that creating a micro cycle for a resource-intensive task is prevented."""
    # Create a resource-intensive task
    resource_intensive_task = {
        "description": "Resource intensive task",
        "resource_usage": 0.9,
    }

    # Attempt to create a micro cycle
    try:
        context.exception = None
        context.edrr_coordinator.create_micro_cycle(
            resource_intensive_task, Phase.EXPAND
        )
    except EDRRCoordinatorError as e:
        context.exception = e

    # Verify that an exception was raised
    assert context.exception is not None
    assert "resource" in str(context.exception).lower()


@then("creating a micro cycle for a lightweight task should be allowed")
def verify_lightweight_task_allowed(context):
    """Verify that creating a micro cycle for a lightweight task is allowed."""
    # Create a lightweight task
    lightweight_task = {"description": "Lightweight task", "resource_usage": 0.2}

    # Attempt to create a micro cycle
    try:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(
            lightweight_task, Phase.EXPAND
        )
        assert micro_cycle is not None
    except Exception as e:
        pytest.fail(
            f"Creating a micro cycle for a lightweight task raised an exception: {e}"
        )


@then("creating a micro cycle with human override to terminate should be prevented")
def verify_human_override_terminate(context):
    """Verify that creating a micro cycle with human override to terminate is prevented."""
    # Create a task with human override to terminate
    override_task = {"description": "Task with override", "human_override": "terminate"}

    # Attempt to create a micro cycle
    try:
        context.exception = None
        context.edrr_coordinator.create_micro_cycle(override_task, Phase.EXPAND)
    except EDRRCoordinatorError as e:
        context.exception = e

    # Verify that an exception was raised
    assert context.exception is not None
    assert "human override" in str(context.exception).lower()


@then("creating a micro cycle with human override to continue should be allowed")
def verify_human_override_continue(context):
    """Verify that creating a micro cycle with human override to continue is allowed."""
    # Create a task with human override to continue
    override_task = {"description": "Task with override", "human_override": "continue"}

    # Attempt to create a micro cycle
    try:
        micro_cycle = context.edrr_coordinator.create_micro_cycle(
            override_task, Phase.EXPAND
        )
        assert micro_cycle is not None
    except Exception as e:
        pytest.fail(
            f"Creating a micro cycle with human override to continue raised an exception: {e}"
        )
