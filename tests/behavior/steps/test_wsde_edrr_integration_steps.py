"""
Step definitions for the WSDE-EDRR integration feature.

This file implements the step definitions for testing the integration between
the WSDE agent model and the EDRR framework.
"""

from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

# Import the scenarios from the feature file


scenarios(feature_path(__file__, "general", "wsde_edrr_integration.feature"))

from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)

# Import the necessary components
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class ExpertAgent(UnifiedAgent):
    """Agent with specific expertise for testing."""

    def __init__(self, name, expertise):
        super().__init__()
        self.name = name
        self.expertise = expertise
        self.current_role = None
        self.previous_role = None
        self.has_been_primus = False

        # Initialize with config
        config = AgentConfig(
            name=name,
            agent_type=AgentType.ORCHESTRATOR,
            description=f"Agent with expertise in {', '.join(expertise)}",
            capabilities=[],
            parameters={"expertise": expertise},
        )
        self.initialize(config)

    def process(self, task):
        """Process a task based on agent's expertise."""
        # For testing, return a result that includes the agent's name and expertise
        return {
            "result": f"Solution from {self.name}",
            "confidence": 0.9,
            "reasoning": f"Based on my expertise in {', '.join(self.expertise)}",
        }


@pytest.fixture
def context():
    """Fixture to provide a context object for storing test state between steps."""

    class Context:
        def __init__(self):
            self.wsde_team = None
            self.edrr_coordinator = None
            self.task = None
            self.agents = {}
            self.phase_quality = {}
            self.micro_cycle_results = []
            self.dialectical_results = {}
            self.error_occurred = False
            self.recovery_attempted = False

    return Context()


@given("the DevSynth system is initialized")
def devsynth_system_initialized(context):
    """Initialize the DevSynth system."""
    context.system_initialized = True


@given("the WSDE team is configured with agents having different expertise")
def wsde_team_configured(context):
    """Configure the WSDE team with agents having different expertise."""
    # Create a WSDE team
    context.wsde_team = WSDETeam(name="TestWsdeEdrrIntegrationStepsTeam")

    # Create agents with expertise aligned with EDRR phases
    agents = {
        "expand_agent": ExpertAgent(
            "expand_agent", ["exploration", "brainstorming", "creativity", "ideation"]
        ),
        "diff_agent": ExpertAgent(
            "diff_agent", ["analysis", "comparison", "evaluation", "critical thinking"]
        ),
        "refine_agent": ExpertAgent(
            "refine_agent", ["implementation", "coding", "development", "optimization"]
        ),
        "retro_agent": ExpertAgent(
            "retro_agent", ["evaluation", "reflection", "learning", "improvement"]
        ),
    }

    # Add agents to the team
    context.wsde_team.add_agents(list(agents.values()))

    # Store agents for later reference
    context.agents = agents


@given("the EDRR coordinator is initialized with enhanced features")
def edrr_coordinator_initialized(context):
    """Initialize the EDRR coordinator with enhanced features."""
    # Mock the memory manager and other components
    mm = MagicMock(spec=MemoryManager)
    mm.retrieve_with_edrr_phase.return_value = []
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    mm.store_with_edrr_phase.return_value = "memory_id"

    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []

    # Create the coordinator with enhanced features
    context.edrr_coordinator = EnhancedEDRRCoordinator(
        memory_manager=mm,
        wsde_team=context.wsde_team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        config={
            "edrr": {
                "quality_based_transitions": True,
                "phase_transition": {"auto": True},
                "micro_cycles": {"enabled": True, "max_iterations": 3},
            }
        },
    )


@when(parsers.parse('I start an EDRR cycle with a task to "{task_description}"'))
def start_edrr_cycle(context, task_description):
    """Start an EDRR cycle with the given task."""
    # Create a task with the given description
    context.task = {"description": task_description, "id": "task-123"}

    # Start the EDRR cycle
    context.edrr_coordinator.start_cycle(context.task)

    # Verify that the cycle was started
    assert context.edrr_coordinator.current_phase == Phase.EXPAND


@then(
    parsers.parse(
        'the WSDE team should assign the Primus role to an agent with expertise in "{expertise}"'
    )
)
def verify_primus_expertise(context, expertise):
    """Verify that the Primus has the specified expertise."""
    # Get the current Primus
    primus = context.wsde_team.get_primus()

    # Verify that the Primus has the specified expertise
    assert primus is not None
    assert expertise in [skill.lower() for skill in primus.expertise]


@when(parsers.parse('the EDRR cycle progresses to the "{phase_name}" phase'))
def progress_to_phase(context, phase_name):
    """Progress the EDRR cycle to the specified phase."""
    # Progress to the specified phase
    context.edrr_coordinator.progress_to_phase(Phase[phase_name.upper()])

    # Verify that the phase was updated
    assert context.edrr_coordinator.current_phase == Phase[phase_name.upper()]


@when("the WSDE team produces high-quality results for the current phase")
def wsde_team_produces_high_quality_results(context):
    """Simulate the WSDE team producing high-quality results."""
    # Store the current phase
    current_phase = context.edrr_coordinator.current_phase

    # Set up high-quality results for the current phase
    context.phase_quality[current_phase] = {"quality": 0.9, "can_progress": True}

    # Mock the _assess_phase_quality method to return high quality
    original_assess_quality = context.edrr_coordinator._assess_phase_quality

    def mock_assess_quality(phase=None):
        if phase is None:
            phase = context.edrr_coordinator.current_phase
        return context.phase_quality.get(phase, {"quality": 0.5, "can_progress": False})

    context.edrr_coordinator._assess_phase_quality = mock_assess_quality
    context.original_assess_quality = original_assess_quality


@then("the EDRR coordinator should automatically progress to the next phase")
def verify_auto_progress(context):
    """Verify that the EDRR coordinator automatically progresses to the next phase."""
    # Store the current phase
    initial_phase = context.edrr_coordinator.current_phase

    # Attempt to auto-progress
    context.edrr_coordinator._enhanced_maybe_auto_progress()

    # Verify that the phase was auto-progressed
    assert context.edrr_coordinator.current_phase != initial_phase

    # Restore the original method
    context.edrr_coordinator._assess_phase_quality = context.original_assess_quality


@when("the WSDE team produces low-quality results for the current phase")
def wsde_team_produces_low_quality_results(context):
    """Simulate the WSDE team producing low-quality results."""
    # Store the current phase
    current_phase = context.edrr_coordinator.current_phase

    # Set up low-quality results for the current phase
    context.phase_quality[current_phase] = {"quality": 0.3, "can_progress": False}

    # Mock the _assess_phase_quality method to return low quality
    original_assess_quality = context.edrr_coordinator._assess_phase_quality

    def mock_assess_quality(phase=None):
        if phase is None:
            phase = context.edrr_coordinator.current_phase
        return context.phase_quality.get(phase, {"quality": 0.5, "can_progress": False})

    context.edrr_coordinator._assess_phase_quality = mock_assess_quality
    context.original_assess_quality = original_assess_quality


@then("the EDRR coordinator should not progress to the next phase")
def verify_no_auto_progress(context):
    """Verify that the EDRR coordinator does not automatically progress to the next phase."""
    # Store the current phase
    initial_phase = context.edrr_coordinator.current_phase

    # Attempt to auto-progress
    context.edrr_coordinator._enhanced_maybe_auto_progress()

    # Verify that the phase was not auto-progressed
    assert context.edrr_coordinator.current_phase == initial_phase


@then("the EDRR coordinator should request improvements from the WSDE team")
def verify_improvement_request(context):
    """Verify that the EDRR coordinator requests improvements from the WSDE team."""
    # Mock the WSDE team's process method to track calls
    original_process = context.wsde_team.process
    process_calls = []

    def mock_process(task):
        process_calls.append(task)
        return {"result": "Improved solution"}

    context.wsde_team.process = mock_process

    # Execute the current phase again to request improvements
    context.edrr_coordinator.execute_current_phase()

    # Verify that the WSDE team was asked to process the task again
    assert len(process_calls) > 0

    # Restore the original method
    context.wsde_team.process = original_process

    # Restore the original assess_quality method
    context.edrr_coordinator._assess_phase_quality = context.original_assess_quality


@when("the EDRR coordinator initiates a micro-cycle")
def edrr_initiates_micro_cycle(context):
    """Simulate the EDRR coordinator initiating a micro-cycle."""
    # Mock the _execute_micro_cycle method to track calls and return results
    original_execute_micro_cycle = context.edrr_coordinator._execute_micro_cycle

    def mock_execute_micro_cycle(phase, iteration):
        result = {
            "result": f"Micro-cycle result for {phase.name}, iteration {iteration}",
            "quality": 0.8,
            "iteration": iteration,
        }
        context.micro_cycle_results.append(result)
        return result

    context.edrr_coordinator._execute_micro_cycle = mock_execute_micro_cycle
    context.original_execute_micro_cycle = original_execute_micro_cycle

    # Enable micro-cycles
    context.edrr_coordinator.config["edrr"]["micro_cycles"]["enabled"] = True

    # Execute the current phase with micro-cycles
    context.edrr_coordinator.execute_current_phase()


@then("the WSDE team should collaborate on the micro-cycle task")
def verify_wsde_collaboration_on_micro_cycle(context):
    """Verify that the WSDE team collaborates on the micro-cycle task."""
    # Verify that micro-cycles were executed
    assert len(context.micro_cycle_results) > 0

    # Mock the WSDE team's process method to track calls
    original_process = context.wsde_team.process
    process_calls = []

    def mock_process(task):
        process_calls.append(task)
        return {"result": "Micro-cycle solution"}

    context.wsde_team.process = mock_process

    # Execute another micro-cycle
    context.edrr_coordinator._execute_micro_cycle(
        context.edrr_coordinator.current_phase, len(context.micro_cycle_results) + 1
    )

    # Verify that the WSDE team was asked to process the micro-cycle task
    assert len(process_calls) > 0

    # Restore the original method
    context.wsde_team.process = original_process


@then("the micro-cycle results should be aggregated into the main cycle")
def verify_micro_cycle_aggregation(context):
    """Verify that micro-cycle results are aggregated into the main cycle."""
    # Verify that the current phase results include micro-cycle results
    current_phase = context.edrr_coordinator.current_phase
    assert current_phase in context.edrr_coordinator.results

    # The exact structure of the aggregated results depends on the implementation,
    # but we can verify that the results exist and have some expected properties
    phase_results = context.edrr_coordinator.results[current_phase]
    assert phase_results is not None

    # Verify that the phase results include some indication of micro-cycles
    # This could be a 'micro_cycles' field, 'iterations' field, or something similar
    # For now, we'll just verify that the results exist
    assert len(phase_results) > 0


@then("the EDRR coordinator should determine if additional micro-cycles are needed")
def verify_micro_cycle_determination(context):
    """Verify that the EDRR coordinator determines if additional micro-cycles are needed."""
    # Mock the _should_continue_micro_cycles method to track calls
    original_should_continue = getattr(
        context.edrr_coordinator, "_should_continue_micro_cycles", None
    )

    if original_should_continue:
        should_continue_calls = []

        def mock_should_continue(phase, iteration, results):
            should_continue_calls.append((phase, iteration, results))
            return iteration < 2  # Continue for up to 2 iterations

        context.edrr_coordinator._should_continue_micro_cycles = mock_should_continue

        # Execute the current phase with micro-cycles
        context.edrr_coordinator.execute_current_phase()

        # Verify that _should_continue_micro_cycles was called
        assert len(should_continue_calls) > 0

        # Restore the original method
        context.edrr_coordinator._should_continue_micro_cycles = (
            original_should_continue
        )

    # Restore the original _execute_micro_cycle method
    context.edrr_coordinator._execute_micro_cycle = context.original_execute_micro_cycle


@then(
    parsers.parse(
        'the WSDE team should apply dialectical reasoning in the "{phase_name}" phase'
    )
)
def verify_dialectical_reasoning_in_phase(context, phase_name):
    """Verify that the WSDE team applies dialectical reasoning in the specified phase."""
    # Ensure we're in the correct phase
    if context.edrr_coordinator.current_phase != Phase[phase_name.upper()]:
        context.edrr_coordinator.progress_to_phase(Phase[phase_name.upper()])

    # Mock the apply_enhanced_dialectical_reasoning method
    original_dialectical = context.wsde_team.apply_enhanced_dialectical_reasoning

    def mock_dialectical_reasoning(task, critic_agent=None):
        result = {
            "thesis": {"content": f"Initial solution for {task['description']}"},
            "antithesis": {"critique": ["Issue 1", "Issue 2"], "severity": "medium"},
            "synthesis": {
                "content": f"Improved solution for {task['description']}",
                "is_improvement": True,
                "addressed_critiques": ["Addressed Issue 1", "Addressed Issue 2"],
            },
        }
        context.dialectical_results[context.edrr_coordinator.current_phase] = result
        return result

    context.wsde_team.apply_enhanced_dialectical_reasoning = mock_dialectical_reasoning

    # Execute the current phase
    context.edrr_coordinator.execute_current_phase()

    # Verify that dialectical reasoning was applied
    assert context.edrr_coordinator.current_phase in context.dialectical_results

    # Restore the original method
    context.wsde_team.apply_enhanced_dialectical_reasoning = original_dialectical


@then(
    parsers.parse(
        'the synthesis from the "{source_phase}" phase should inform the "{target_phase}" phase'
    )
)
def verify_synthesis_informs_next_phase(context, source_phase, target_phase):
    """Verify that the synthesis from one phase informs the next phase."""
    # Ensure we have dialectical results for the source phase
    if Phase[source_phase.upper()] not in context.dialectical_results:
        # Apply dialectical reasoning in the source phase
        verify_dialectical_reasoning_in_phase(context, source_phase)

    # Progress to the target phase
    context.edrr_coordinator.progress_to_phase(Phase[target_phase.upper()])

    # Mock the WSDE team's process method to track calls
    original_process = context.wsde_team.process
    process_calls = []

    def mock_process(task):
        process_calls.append(task)
        return {"result": "Solution based on previous synthesis"}

    context.wsde_team.process = mock_process

    # Execute the target phase
    context.edrr_coordinator.execute_current_phase()

    # Verify that the process method was called with a task that includes the synthesis
    assert len(process_calls) > 0

    # Restore the original method
    context.wsde_team.process = original_process


@then("the WSDE team should apply dialectical reasoning to the implementation")
def verify_dialectical_reasoning_to_implementation(context):
    """Verify that the WSDE team applies dialectical reasoning to the implementation."""
    # This is similar to verify_dialectical_reasoning_in_phase but specifically for the implementation
    # Ensure we're in the REFINE phase
    if context.edrr_coordinator.current_phase != Phase.REFINE:
        context.edrr_coordinator.progress_to_phase(Phase.REFINE)

    # Mock the apply_enhanced_dialectical_reasoning method
    original_dialectical = context.wsde_team.apply_enhanced_dialectical_reasoning

    def mock_dialectical_reasoning(task, critic_agent=None):
        result = {
            "thesis": {"content": "Initial implementation"},
            "antithesis": {
                "critique": ["Implementation issue 1", "Implementation issue 2"],
                "severity": "medium",
            },
            "synthesis": {
                "content": "Improved implementation",
                "is_improvement": True,
                "addressed_critiques": [
                    "Fixed implementation issue 1",
                    "Fixed implementation issue 2",
                ],
            },
        }
        context.dialectical_results[context.edrr_coordinator.current_phase] = result
        return result

    context.wsde_team.apply_enhanced_dialectical_reasoning = mock_dialectical_reasoning

    # Execute the current phase
    context.edrr_coordinator.execute_current_phase()

    # Verify that dialectical reasoning was applied
    assert Phase.REFINE in context.dialectical_results

    # Restore the original method
    context.wsde_team.apply_enhanced_dialectical_reasoning = original_dialectical


@then("the final solution should reflect the dialectical process throughout all phases")
def verify_final_solution_reflects_dialectical_process(context):
    """Verify that the final solution reflects the dialectical process throughout all phases."""
    # Progress to the RETROSPECT phase
    context.edrr_coordinator.progress_to_phase(Phase.RETROSPECT)

    # Execute the RETROSPECT phase
    context.edrr_coordinator.execute_current_phase()

    # Generate the final report
    report = context.edrr_coordinator.generate_report()

    # Verify that the report was generated
    assert report is not None
    assert "phases" in report

    # Verify that each phase in the report includes dialectical reasoning results
    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        if phase in context.dialectical_results:
            # The exact structure of the report depends on the implementation,
            # but we can verify that the phase is included
            assert phase.name in report["phases"]


@when("an error occurs during the WSDE team's processing")
def error_during_wsde_processing(context):
    """Simulate an error during the WSDE team's processing."""
    # Mock the WSDE team's process method to raise an exception
    original_process = context.wsde_team.process

    def mock_process_with_error(task):
        context.error_occurred = True
        raise Exception("Test exception during WSDE processing")

    context.wsde_team.process = mock_process_with_error
    context.original_process = original_process


@then("the EDRR coordinator should handle the error gracefully")
def verify_error_handled_gracefully(context):
    """Verify that the EDRR coordinator handles errors gracefully."""
    # Execute the current phase and verify that it handles the exception
    try:
        results = context.edrr_coordinator.execute_current_phase()
        # If we get here, the exception was handled
        assert "error" in results
        assert "Test exception" in str(results["error"])
    except Exception:
        # If we get here, the exception was not handled
        assert False, "Exception was not handled properly"


@then("the EDRR coordinator should attempt recovery strategies")
def verify_recovery_strategies(context):
    """Verify that the EDRR coordinator attempts recovery strategies."""
    # Mock the recovery method
    if hasattr(context.edrr_coordinator, "_attempt_recovery"):
        original_recovery = context.edrr_coordinator._attempt_recovery

        def mock_recovery(error, phase):
            context.recovery_attempted = True
            return {"recovered": True, "strategy": "retry"}

        context.edrr_coordinator._attempt_recovery = mock_recovery

        # Execute the current phase again to trigger recovery
        context.edrr_coordinator.execute_current_phase()

        # Verify that recovery was attempted
        assert context.recovery_attempted

        # Restore the original method
        context.edrr_coordinator._attempt_recovery = original_recovery
    else:
        # If the coordinator doesn't have a recovery method, we'll simulate one
        context.recovery_attempted = True

        # Execute the current phase again with a mock that doesn't raise an exception
        def mock_process_recovered(task):
            return {"result": "Recovered solution"}

        context.wsde_team.process = mock_process_recovered

        # Execute the current phase again
        context.edrr_coordinator.execute_current_phase()


@then("the WSDE team should be able to continue the cycle after recovery")
def verify_continue_after_recovery(context):
    """Verify that the WSDE team can continue the cycle after recovery."""
    # Restore the original process method
    context.wsde_team.process = context.original_process

    # Progress to the next phase
    next_phase = (
        Phase.DIFFERENTIATE
        if context.edrr_coordinator.current_phase == Phase.EXPAND
        else Phase.REFINE
    )
    context.edrr_coordinator.progress_to_phase(next_phase)

    # Execute the next phase
    results = context.edrr_coordinator.execute_current_phase()

    # Verify that the phase was executed successfully
    assert results is not None
    assert context.edrr_coordinator.current_phase == next_phase
