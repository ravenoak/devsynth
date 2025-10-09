import sys
import types

import pytest

openai_mod = types.ModuleType("openai")
setattr(openai_mod, "OpenAI", object)
setattr(openai_mod, "AsyncOpenAI", object)
sys.modules["openai"] = openai_mod
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam


class SimpleMockLLM:

    def generate(self, prompt: str, parameters=None):
        return "mock response"


from devsynth.methodology.base import Phase


@pytest.mark.slow
def test_edrr_cycle_with_mock_llm_succeeds(tmp_path):
    """Test that edrr cycle with mock llm succeeds.

    ReqID: N/A"""
    memory_adapter = TinyDBMemoryAdapter()
    memory_manager = MemoryManager(adapters={"tinydb": memory_adapter})
    wsde_team = WSDETeam(name="TestEdrrMockLlmIntegrationTeam")
    llm = SimpleMockLLM()
    wsde_team.generate_diverse_ideas = (
        lambda task, max_ideas=10, diversity_threshold=0.7: [
            {"id": 1, "idea": llm.generate(task.get("description", ""))}
        ]
    )
    wsde_team.formulate_decision_criteria = lambda task, evaluated_options, trade_offs, contextualize_with_code=True, code_analyzer=None: {
        "criteria": 1
    }
    wsde_team.elaborate_details = lambda selected_option, **kw: [{"step": 1}]
    wsde_team.create_implementation_plan = lambda details, **kw: details
    wsde_team.optimize_implementation = lambda plan, **kw: {"plan": plan}
    wsde_team.perform_quality_assurance = lambda plan, **kw: {}
    wsde_team.extract_learnings = lambda results, **kw: []
    wsde_team.recognize_patterns = lambda learnings, **kw: []
    wsde_team.integrate_knowledge = lambda learnings, patterns, **kw: {}
    wsde_team.generate_improvement_suggestions = lambda *a, **kw: []
    coordinator = EDRRCoordinator(
        memory_manager=memory_manager,
        wsde_team=wsde_team,
        code_analyzer=CodeAnalyzer(),
        ast_transformer=AstTransformer(),
        prompt_manager=PromptManager(),
        documentation_manager=DocumentationManager(memory_manager),
        enable_enhanced_logging=True,
    )
    task = {"description": "demo"}
    coordinator.start_cycle(task)
    for phase in [Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT]:
        coordinator.progress_to_phase(phase)
    report = coordinator.generate_report()
    traces = coordinator.get_execution_traces()
    history = coordinator.get_execution_history()
    assert report["cycle_id"] == coordinator.cycle_id
    assert "EXPAND" in report["phases"]
    assert "RETROSPECT" in report["phases"]
    assert traces.get("cycle_id") == coordinator.cycle_id
    assert len(history) >= 4
