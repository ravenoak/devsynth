"""
Integration test for EDRR with real LLM providers.

This test uses real LLM providers from the provider system to test the EDRR cycle.
It requires valid API keys or endpoints to be configured in environment variables.
"""

import os
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.adapters.provider_system import get_provider, ProviderType
from devsynth.methodology.base import Phase
from devsynth.domain.models.memory import MemoryType


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LM_STUDIO_ENDPOINT"),
    reason="No LLM provider configured. Set OPENAI_API_KEY or LM_STUDIO_ENDPOINT."
)
def test_edrr_cycle_with_real_llm(tmp_path):
    """
    Test EDRR cycle with a real LLM provider and verify memory integration.

    This test will use the configured LLM provider (OpenAI or LM Studio)
    to run a complete EDRR cycle with a simple task. It also verifies that
    the results are properly stored in and retrieved from the memory system
    with the correct EDRR phase tags.

    It requires either OPENAI_API_KEY or LM_STUDIO_ENDPOINT to be set.
    """
    # Set up memory components with both TinyDB and Graph adapters
    tinydb_adapter = TinyDBMemoryAdapter()
    graph_adapter = GraphMemoryAdapter(base_path=str(tmp_path / "graph_memory"))
    memory_manager = MemoryManager(adapters={
        "tinydb": tinydb_adapter,
        "graph": graph_adapter
    })

    # Create WSDE team
    wsde_team = WSDETeam()

    # Get a real LLM provider
    provider = get_provider(fallback=True)

    # Create a simple task for testing
    task = {
        "description": "Create a function to calculate the factorial of a number",
        "language": "python",
        "complexity": "medium"
    }

    # Create EDRR coordinator
    coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(memory_manager),
        enable_enhanced_logging=True,
    )

    # Start EDRR cycle
    coordinator.start_cycle(task)

    # Verify that EXPAND phase results are stored in memory
    expand_results = memory_manager.retrieve_with_edrr_phase(
        "EXPAND_RESULTS", "EXPAND", {"cycle_id": coordinator.cycle_id}
    )
    assert expand_results, "EXPAND phase results not found in memory"
    assert "ideas" in expand_results, "EXPAND phase results missing 'ideas' key"
    assert "knowledge" in expand_results, "EXPAND phase results missing 'knowledge' key"

    # Progress through all phases
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        coordinator.progress_to_phase(phase)

        # Verify that phase results are stored in memory
        phase_results = memory_manager.retrieve_with_edrr_phase(
            f"{phase.value}_RESULTS", phase.value, {"cycle_id": coordinator.cycle_id}
        )
        assert phase_results, f"{phase.value} phase results not found in memory"

    # Generate report and get execution traces
    report = coordinator.generate_report()
    traces = coordinator.get_execution_traces()
    history = coordinator.get_execution_history()

    # Verify results
    assert report["cycle_id"] == coordinator.cycle_id
    assert "EXPAND" in report["phases"]
    assert "DIFFERENTIATE" in report["phases"]
    assert "REFINE" in report["phases"]
    assert "RETROSPECT" in report["phases"]
    assert traces.get("cycle_id") == coordinator.cycle_id
    assert len(history) >= 4

    # Verify that the report contains meaningful content
    assert "factorial" in str(report).lower()

    # Verify that the final solution is a valid Python function
    final_solution = None
    for phase_data in report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    assert "def factorial" in str(final_solution).lower()

    # Verify that the final solution can be retrieved from memory
    refine_results = memory_manager.retrieve_with_edrr_phase(
        "REFINE_RESULTS", "REFINE", {"cycle_id": coordinator.cycle_id}
    )
    assert refine_results, "REFINE phase results not found in memory"
    assert "solution" in refine_results, "REFINE phase results missing 'solution' key"
    assert "def factorial" in str(refine_results["solution"]).lower()

    # Print summary for debugging
    print(f"EDRR cycle completed with provider: {provider.__class__.__name__}")
    print(f"Final solution: {final_solution}")
    print(f"Memory integration verified with GraphMemoryAdapter")


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY") and not os.environ.get("LM_STUDIO_ENDPOINT"),
    reason="No LLM provider configured. Set OPENAI_API_KEY or LM_STUDIO_ENDPOINT."
)
def test_edrr_cycle_with_real_project(tmp_path):
    """
    Test EDRR cycle with a real LLM provider on a more complex project.

    This test creates a small project with multiple files and asks the EDRR
    framework to analyze and improve it. This tests the framework's ability
    to handle more realistic and complex tasks.

    It requires either OPENAI_API_KEY or LM_STUDIO_ENDPOINT to be set.
    """
    # Create a small project with multiple files
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(exist_ok=True)

    # Create a simple Flask application with some issues
    app_py = project_dir / "app.py"
    app_py.write_text("""
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
""")

    # Create a requirements.txt file
    requirements_txt = project_dir / "requirements.txt"
    requirements_txt.write_text("""
flask==2.0.1
""")

    # Set up memory components
    memory_adapter = TinyDBMemoryAdapter()
    memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})

    # Create WSDE team
    wsde_team = WSDETeam()

    # Get a real LLM provider
    provider = get_provider(fallback=True)

    # Create a complex task for testing
    task = {
        "description": "Analyze the Flask application and improve it by adding proper data validation, error handling, and following best practices for Flask applications.",
        "project_path": str(project_dir),
        "language": "python",
        "complexity": "high"
    }

    # Create EDRR coordinator
    coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(memory_manager),
        enable_enhanced_logging=True,
    )

    # Start EDRR cycle
    coordinator.start_cycle(task)

    # Progress through all phases
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        coordinator.progress_to_phase(phase)

    # Generate report and get execution traces
    report = coordinator.generate_report()
    traces = coordinator.get_execution_traces()
    history = coordinator.get_execution_history()

    # Verify results
    assert report["cycle_id"] == coordinator.cycle_id
    assert "EXPAND" in report["phases"]
    assert "DIFFERENTIATE" in report["phases"]
    assert "REFINE" in report["phases"]
    assert "RETROSPECT" in report["phases"]
    assert traces.get("cycle_id") == coordinator.cycle_id
    assert len(history) >= 4

    # Verify that the report contains meaningful content related to Flask
    report_str = str(report).lower()
    assert "flask" in report_str
    assert "validation" in report_str

    # Verify that the final solution addresses the issues
    final_solution = None
    for phase_data in report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]

    assert final_solution is not None
    final_solution_str = str(final_solution).lower()

    # Check for improvements in the solution
    assert "validation" in final_solution_str or "validate" in final_solution_str
    assert "error" in final_solution_str and "handling" in final_solution_str

    # Print summary for debugging
    print(f"EDRR cycle completed with provider: {provider.__class__.__name__}")
    print(f"Project analysis and improvement completed")
