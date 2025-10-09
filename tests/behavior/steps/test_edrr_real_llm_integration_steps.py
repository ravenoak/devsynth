import os
import tempfile
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = [pytest.mark.fast]

scenarios(feature_path(__file__, "general", "edrr_real_llm_integration.feature"))

from devsynth.adapters.provider_system import ProviderType, get_provider
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.fixture
def context():
    """Fixture to provide a context object for storing test state between steps."""

    class Context:
        def __init__(self):
            self.memory_adapter = None
            self.memory_manager = None
            self.wsde_team = None
            self.provider = None
            self.coordinator = None
            self.project_dir = None
            self.graph_memory_adapter = None
            self.task = None
            self.report = None
            self.traces = None
            self.history = None

    return Context()


# Skip scenarios if no live LLM provider is configured
@pytest.fixture(autouse=True)
def check_llm_provider(monkeypatch):
    """Skip these steps if neither OpenAI nor LM Studio is configured."""
    # Unset the mock environment variables set by the patch_env_and_cleanup fixture
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LM_STUDIO_ENDPOINT", raising=False)

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get(
        "LM_STUDIO_ENDPOINT"
    ):
        pytest.skip(
            "No LLM provider configured. Set OPENAI_API_KEY or LM_STUDIO_ENDPOINT."
        )


@given("an initialized EDRR coordinator with real LLM provider")
@pytest.mark.medium
def step_initialized_edrr_coordinator_with_real_llm(context):
    # Set up memory components
    context.memory_adapter = TinyDBMemoryAdapter()
    context.memory_manager = MemoryManager(adapters={"tinydb": context.memory_adapter})

    # Create WSDE team
    context.wsde_team = WSDETeam(name="EdrrRealLlmIntegrationStepsTeam")

    # Get a real LLM provider
    context.provider = get_provider(fallback=True)

    # Create EDRR coordinator
    context.coordinator = EDRRCoordinator(
        memory_manager=context.memory_manager,
        wsde_team=context.wsde_team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(context.memory_manager),
        enable_enhanced_logging=True,
    )


@given("a sample Flask application with code quality issues")
@pytest.mark.medium
def step_sample_flask_application(context):
    # Create a temporary directory for the project
    context.project_dir = Path(tempfile.mkdtemp()) / "test_project"
    context.project_dir.mkdir(exist_ok=True)

    # Create a simple Flask application with some issues
    app_py = context.project_dir / "app.py"
    app_py.write_text(
        """
from flask import Flask, request, jsonify

app = Flask(__name__)

# Global variable (not ideal for Flask apps)
users = []

@app.route('/users', methods=['GET'])
def get_users():
    return jsonify(users)

@app.route('/users', methods=['POST'])
def create_user():
    user = request.json
    # No validation of user data
    users.append(user)
    return jsonify(user), 201

if __name__ == '__main__':
    app.run(debug=True)
"""
    )

    # Create a requirements.txt file
    requirements_txt = context.project_dir / "requirements.txt"
    requirements_txt.write_text(
        """
flask==2.0.1
"""
    )


@given("a configured graph memory system")
@pytest.mark.medium
def step_configured_graph_memory_system(context):
    # Create a new memory manager with both adapters
    context.graph_memory_adapter = GraphMemoryAdapter()
    context.memory_adapter = TinyDBMemoryAdapter()
    context.memory_manager = MemoryManager(
        adapters={
            "tinydb": context.memory_adapter,
            "graph": context.graph_memory_adapter,
        }
    )


@when(parsers.parse('I start an EDRR cycle for "{task_description}"'))
@pytest.mark.medium
def step_start_edrr_cycle(context, task_description):
    # Create a task for testing
    context.task = {
        "description": task_description,
        "language": "python",
        "complexity": "medium",
    }

    # Start EDRR cycle
    context.coordinator.start_cycle(context.task)


@when(parsers.parse('I start an EDRR cycle to "{task_description}"'))
@pytest.mark.medium
def step_start_edrr_cycle_for_project(context, task_description):
    # Create a task for testing with project path
    context.task = {
        "description": task_description,
        "project_path": str(context.project_dir),
        "language": "python",
        "complexity": "high",
    }

    # Start EDRR cycle
    context.coordinator.start_cycle(context.task)


@when("I progress through all EDRR phases")
@pytest.mark.medium
def step_progress_through_all_phases(context):
    # Progress through all phases
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        context.coordinator.progress_to_phase(phase)

    # Generate report and get execution traces
    context.report = context.coordinator.generate_report()
    context.traces = context.coordinator.get_execution_traces()
    context.history = context.coordinator.get_execution_history()


@then("the cycle should complete successfully")
@pytest.mark.medium
def step_cycle_completes_successfully(context):
    # Verify results
    assert context.report["cycle_id"] == context.coordinator.cycle_id
    assert "EXPAND" in context.report["phases"]
    assert "DIFFERENTIATE" in context.report["phases"]
    assert "REFINE" in context.report["phases"]
    assert "RETROSPECT" in context.report["phases"]
    assert context.traces.get("cycle_id") == context.coordinator.cycle_id
    assert len(context.history) >= 4


@then("the final solution should contain a factorial function")
@pytest.mark.medium
def step_solution_contains_factorial(context):
    # Get the final solution
    final_solution = None
    for phase_data in context.report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    assert "def factorial" in str(final_solution).lower()


@then("the solution should handle edge cases")
@pytest.mark.medium
def step_solution_handles_edge_cases(context):
    # Get the final solution
    final_solution = None
    for phase_data in context.report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    final_solution_str = str(final_solution).lower()

    # Check for edge case handling (0, negative numbers, etc.)
    assert any(
        term in final_solution_str
        for term in ["if n < 0", "if n <= 0", "raise", "error", "exception", "edge"]
    )


@then("the final solution should address validation issues")
@pytest.mark.medium
def step_solution_addresses_validation(context):
    # Get the final solution
    final_solution = None
    for phase_data in context.report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    final_solution_str = str(final_solution).lower()

    # Check for validation
    assert "validation" in final_solution_str or "validate" in final_solution_str


@then("the final solution should include error handling")
@pytest.mark.medium
def step_solution_includes_error_handling(context):
    # Get the final solution
    final_solution = None
    for phase_data in context.report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    final_solution_str = str(final_solution).lower()

    # Check for error handling
    assert "error" in final_solution_str and "handling" in final_solution_str


@then("the final solution should follow Flask best practices")
@pytest.mark.medium
def step_solution_follows_flask_best_practices(context):
    # Get the final solution
    final_solution = None
    for phase_data in context.report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    final_solution_str = str(final_solution).lower()

    # Check for Flask best practices
    best_practices = [
        "blueprint",
        "app.config",
        "error_handler",
        "jsonify",
        "request.get_json",
        "http",
        "status",
        "flask-sqlalchemy",
        "model",
    ]
    assert any(practice in final_solution_str for practice in best_practices)


@then("the memory system should store phase results correctly")
@pytest.mark.medium
def step_memory_system_stores_results(context):
    # Check that the memory system has stored the phase results
    if hasattr(context, "graph_memory_adapter"):
        # For graph memory adapter
        items = context.graph_memory_adapter.search({})
        assert len(items) > 0

    # Check tinydb adapter
    records = context.memory_adapter.search({})
    assert len(records) > 0

    # Check that the cycle_id is in the records
    cycle_records = [
        r for r in records if r.metadata.get("cycle_id") == context.coordinator.cycle_id
    ]
    assert len(cycle_records) > 0


@then("the final solution should reference previous phase insights")
@pytest.mark.medium
def step_solution_references_previous_insights(context):
    # Get the final solution and phase data
    final_solution = None
    expand_phase_data = context.report["phases"].get("EXPAND", {})
    differentiate_phase_data = context.report["phases"].get("DIFFERENTIATE", {})

    for phase_data in context.report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    final_solution_str = str(final_solution).lower()

    # Check that insights from previous phases are referenced in the final solution
    if "insights" in expand_phase_data:
        expand_insights = str(expand_phase_data["insights"]).lower()
        # Extract key terms from expand insights
        key_terms = [term for term in expand_insights.split() if len(term) > 5]
        # Check if any key terms appear in the final solution
        assert any(term in final_solution_str for term in key_terms)

    if "insights" in differentiate_phase_data:
        differentiate_insights = str(differentiate_phase_data["insights"]).lower()
        # Extract key terms from differentiate insights
        key_terms = [term for term in differentiate_insights.split() if len(term) > 5]
        # Check if any key terms appear in the final solution
        assert any(term in final_solution_str for term in key_terms)
