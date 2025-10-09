"""
Integration test for EDRR with real LLM providers.

This test uses real LLM providers from the provider system to test the EDRR cycle.
It requires valid API keys or endpoints to be configured in environment variables.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

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
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


@pytest.mark.parametrize(
    "provider_resource",
    [
        pytest.param("openai", marks=pytest.mark.requires_resource("openai")),
        pytest.param("lmstudio", marks=pytest.mark.requires_resource("lmstudio")),
    ],
)
@pytest.mark.slow
def test_edrr_cycle_with_real_llm_has_expected(tmp_path, provider_resource):
    """Test EDRR cycle with a real LLM provider and verify memory integration.

    This test will use the configured LLM provider (OpenAI or LM Studio)
    to run a complete EDRR cycle with a simple task. It also verifies that
    the results are properly stored in and retrieved from the memory system
    with the correct EDRR phase tags.

    It requires either OPENAI_API_KEY or LM_STUDIO_ENDPOINT to be set.

    ReqID: N/A"""

    tinydb_adapter = TinyDBMemoryAdapter()
    graph_adapter = GraphMemoryAdapter(base_path=str(tmp_path / "graph_memory"))
    memory_manager = MemoryManager(
        adapters={"tinydb": tinydb_adapter, "graph": graph_adapter}
    )
    wsde_team = WSDETeam(name="EDRRTestTeam")
    provider = get_provider(fallback=True)
    task = {
        "description": "Create a function to calculate the factorial of a number",
        "language": "python",
        "complexity": "medium",
    }
    coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(memory_manager),
        enable_enhanced_logging=True,
    )
    coordinator.start_cycle(task)
    expand_results = memory_manager.retrieve_with_edrr_phase(
        MemoryType.EXPAND_RESULTS, "EXPAND", {"cycle_id": coordinator.cycle_id}
    )
    assert expand_results, "EXPAND phase results not found in memory"
    assert "ideas" in expand_results, "EXPAND phase results missing 'ideas' key"
    assert "knowledge" in expand_results, "EXPAND phase results missing 'knowledge' key"
    phase_memory_map = {
        Phase.DIFFERENTIATE: MemoryType.DIFFERENTIATE_RESULTS,
        Phase.REFINE: MemoryType.REFINE_RESULTS,
        Phase.RETROSPECT: MemoryType.RETROSPECT_RESULTS,
    }
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        coordinator.progress_to_phase(phase)
        phase_results = memory_manager.retrieve_with_edrr_phase(
            phase_memory_map[phase], phase.value, {"cycle_id": coordinator.cycle_id}
        )
        assert phase_results, f"{phase.value} phase results not found in memory"
    report = coordinator.generate_report()
    traces = coordinator.get_execution_traces()
    history = coordinator.get_execution_history()
    assert report["cycle_id"] == coordinator.cycle_id
    assert "EXPAND" in report["phases"]
    assert "DIFFERENTIATE" in report["phases"]
    assert "REFINE" in report["phases"]
    assert "RETROSPECT" in report["phases"]
    assert traces.get("cycle_id") == coordinator.cycle_id
    assert len(history) >= 4
    assert "factorial" in str(report).lower()
    final_solution = None
    for phase_data in report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]
    assert final_solution is not None
    assert "def factorial" in str(final_solution).lower()
    refine_results = memory_manager.retrieve_with_edrr_phase(
        "REFINE_RESULTS", "REFINE", {"cycle_id": coordinator.cycle_id}
    )
    assert refine_results, "REFINE phase results not found in memory"
    assert "solution" in refine_results, "REFINE phase results missing 'solution' key"
    assert "def factorial" in str(refine_results["solution"]).lower()
    print(f"EDRR cycle completed with provider: {provider.__class__.__name__}")
    print(f"Final solution: {final_solution}")
    print(f"Memory integration verified with GraphMemoryAdapter")


@pytest.mark.parametrize(
    "provider_resource",
    [
        pytest.param("openai", marks=pytest.mark.requires_resource("openai")),
        pytest.param("lmstudio", marks=pytest.mark.requires_resource("lmstudio")),
    ],
)
@pytest.mark.slow
def test_edrr_cycle_with_real_project_succeeds(tmp_path, provider_resource):
    """Test EDRR cycle with a real LLM provider on a more complex project.

    This test creates a small project with multiple files and asks the EDRR
    framework to analyze and improve it. This tests the framework's ability
    to handle more realistic and complex tasks.

    It requires either OPENAI_API_KEY or LM_STUDIO_ENDPOINT to be set.

    ReqID: N/A"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(exist_ok=True)
    app_py = project_dir / "app.py"
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
    requirements_txt = project_dir / "requirements.txt"
    requirements_txt.write_text("\nflask==2.0.1\n")
    memory_adapter = TinyDBMemoryAdapter()
    memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    wsde_team = WSDETeam(name="EDRRProjectTestTeam")
    provider = get_provider(fallback=True)
    task = {
        "description": "Analyze the Flask application and improve it by adding proper data validation, error handling, and following best practices for Flask applications.",
        "project_path": str(project_dir),
        "language": "python",
        "complexity": "high",
    }
    coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(memory_manager),
        enable_enhanced_logging=True,
    )
    coordinator.start_cycle(task)
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        coordinator.progress_to_phase(phase)
    report = coordinator.generate_report()
    traces = coordinator.get_execution_traces()
    history = coordinator.get_execution_history()
    assert report["cycle_id"] == coordinator.cycle_id
    assert "EXPAND" in report["phases"]
    assert "DIFFERENTIATE" in report["phases"]
    assert "REFINE" in report["phases"]
    assert "RETROSPECT" in report["phases"]
    assert traces.get("cycle_id") == coordinator.cycle_id
    assert len(history) >= 4
    report_str = str(report).lower()
    assert "flask" in report_str
    assert "validation" in report_str
    final_solution = None
    for phase_data in report["phases"].values():
        if "solution" in phase_data:
            final_solution = phase_data["solution"]
    assert final_solution is not None
    final_solution_str = str(final_solution).lower()
    assert "validation" in final_solution_str or "validate" in final_solution_str
    assert "error" in final_solution_str and "handling" in final_solution_str
    print(f"EDRR cycle completed with provider: {provider.__class__.__name__}")
    print(f"Project analysis and improvement completed")
