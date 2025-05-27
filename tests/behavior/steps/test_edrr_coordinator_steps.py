"""Step definitions for the EDRR Coordinator feature."""

from pytest_bdd import given, when, then, parsers
from pytest_bdd import scenarios

# Import the scenarios from the feature file
scenarios('../features/edrr_coordinator.feature')

# Import the necessary components
from unittest.mock import MagicMock, patch
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager


@given("the EDRR coordinator is initialized")
def edrr_coordinator_initialized(context):
    """Initialize the EDRR coordinator."""
    # We'll implement the EDRRCoordinator class later
    # For now, we'll use a mock
    context.edrr_coordinator = MagicMock()
    context.edrr_coordinator.current_phase = None
    context.edrr_coordinator.task = None
    context.edrr_coordinator.results = {}


@given("the memory system is available")
def memory_system_available(context):
    """Make the memory system available."""
    context.memory_manager = MagicMock(spec=MemoryManager)
    context.edrr_coordinator.memory_manager = context.memory_manager


@given("the WSDE team is available")
def wsde_team_available(context):
    """Make the WSDE team available."""
    context.wsde_team = MagicMock(spec=WSDETeam)
    context.edrr_coordinator.wsde_team = context.wsde_team


@given("the AST analyzer is available")
def ast_analyzer_available(context):
    """Make the AST analyzer available."""
    context.code_analyzer = MagicMock(spec=CodeAnalyzer)
    context.ast_transformer = MagicMock(spec=AstTransformer)
    context.edrr_coordinator.code_analyzer = context.code_analyzer
    context.edrr_coordinator.ast_transformer = context.ast_transformer


@given("the prompt manager is available")
def prompt_manager_available(context):
    """Make the prompt manager available."""
    context.prompt_manager = MagicMock(spec=PromptManager)
    context.edrr_coordinator.prompt_manager = context.prompt_manager


@given("the documentation manager is available")
def documentation_manager_available(context):
    """Make the documentation manager available."""
    context.documentation_manager = MagicMock(spec=DocumentationManager)
    context.edrr_coordinator.documentation_manager = context.documentation_manager


@when(parsers.parse('I start the EDRR cycle with a task to "{task_description}"'))
def start_edrr_cycle(context, task_description):
    """Start the EDRR cycle with a task."""
    context.task = {"id": "task-123", "description": task_description}
    context.edrr_coordinator.start_cycle(context.task)


@given(parsers.parse('the "{phase_name}" phase has completed for a task'))
def phase_completed(context, phase_name):
    """Set up a completed phase."""
    context.task = {"id": "task-123", "description": "analyze a Python file"}
    context.edrr_coordinator.task = context.task
    context.edrr_coordinator.current_phase = Phase[phase_name.upper()]
    context.edrr_coordinator.results[context.edrr_coordinator.current_phase] = {
        "completed": True,
        "outputs": [{"type": "approach", "content": "Sample approach"}]
    }


@when(parsers.parse('the coordinator progresses to the "{phase_name}" phase'))
def progress_to_phase(context, phase_name):
    """Progress to the next phase."""
    context.edrr_coordinator.progress_to_phase(Phase[phase_name.upper()])


@then(parsers.parse('the coordinator should enter the "{phase_name}" phase'))
def verify_phase(context, phase_name):
    """Verify the coordinator has entered the specified phase."""
    assert context.edrr_coordinator.current_phase == Phase[phase_name.upper()]


@then("the coordinator should store the task in memory with EDRR phase {phase_name}")
def verify_task_stored(context, phase_name):
    """Verify the task is stored in memory with the correct EDRR phase."""
    context.memory_manager.store_with_edrr_phase.assert_called_with(
        context.task, "TASK", phase_name.strip('"')
    )


@then("the coordinator should store the phase transition in memory")
def verify_phase_transition_stored(context):
    """Verify the phase transition is stored in memory."""
    context.memory_manager.store_with_edrr_phase.assert_called()


@then("the WSDE team should be instructed to brainstorm approaches")
def verify_wsde_brainstorm(context):
    """Verify the WSDE team is instructed to brainstorm approaches."""
    context.wsde_team.build_consensus.assert_called()


@then("the WSDE team should be instructed to evaluate and compare approaches")
def verify_wsde_evaluate(context):
    """Verify the WSDE team is instructed to evaluate and compare approaches."""
    context.wsde_team.apply_enhanced_dialectical_reasoning_multi.assert_called()


@then("the WSDE team should be instructed to implement the selected approach")
def verify_wsde_implement(context):
    """Verify the WSDE team is instructed to implement the selected approach."""
    context.wsde_team.apply_enhanced_dialectical_reasoning.assert_called()


@then("the WSDE team should be instructed to evaluate the implementation")
def verify_wsde_review(context):
    """Verify the WSDE team is instructed to evaluate the implementation."""
    context.wsde_team.apply_dialectical_reasoning.assert_called()


@then("the AST analyzer should be used to analyze the file structure")
def verify_ast_analyze(context):
    """Verify the AST analyzer is used to analyze the file structure."""
    context.code_analyzer.analyze_file.assert_called()


@then("the AST analyzer should be used to evaluate code quality")
def verify_ast_evaluate(context):
    """Verify the AST analyzer is used to evaluate code quality."""
    context.code_analyzer.analyze_code.assert_called()


@then("the AST analyzer should be used to apply code transformations")
def verify_ast_transform(context):
    """Verify the AST analyzer is used to apply code transformations."""
    context.ast_transformer.rename_identifier.assert_called()


@then("the AST analyzer should be used to verify code quality")
def verify_ast_verify(context):
    """Verify the AST analyzer is used to verify code quality."""
    context.ast_transformer.validate_syntax.assert_called()


@then(parsers.parse('the prompt manager should provide templates for the "{phase_name}" phase'))
def verify_prompt_templates(context, phase_name):
    """Verify the prompt manager provides templates for the specified phase."""
    context.prompt_manager.list_templates.assert_called_with(edrr_phase=phase_name.upper())


@then("the documentation manager should retrieve relevant documentation")
def verify_documentation_retrieve(context):
    """Verify the documentation manager retrieves relevant documentation."""
    context.documentation_manager.query_documentation.assert_called()


@then("the documentation manager should retrieve best practices documentation")
def verify_documentation_best_practices(context):
    """Verify the documentation manager retrieves best practices documentation."""
    context.documentation_manager.query_documentation.assert_called()


@then("the documentation manager should retrieve implementation examples")
def verify_documentation_examples(context):
    """Verify the documentation manager retrieves implementation examples."""
    context.documentation_manager.query_documentation.assert_called()


@then("the documentation manager should retrieve evaluation criteria")
def verify_documentation_criteria(context):
    """Verify the documentation manager retrieves evaluation criteria."""
    context.documentation_manager.query_documentation.assert_called()


@then(parsers.parse('the results should be stored in memory with EDRR phase "{phase_name}"'))
def verify_results_stored(context, phase_name):
    """Verify the results are stored in memory with the correct EDRR phase."""
    context.memory_manager.store_with_edrr_phase.assert_called()


@then("a final report should be generated summarizing the entire EDRR cycle")
def verify_final_report(context):
    """Verify a final report is generated."""
    context.edrr_coordinator.generate_report.assert_called()