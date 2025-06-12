import pytest
from unittest.mock import MagicMock

from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager

class SimpleAgent:
    def __init__(self, name):
        self.name = name
        self.expertise = []
        self.current_role = None
    def process(self, task):
        return {"processed_by": self.name}

@pytest.fixture
def coordinator():
    team = WSDETeam()
    team.add_agent(SimpleAgent("agent1"))
    team.generate_diverse_ideas = MagicMock(return_value=["idea"])
    team.create_comparison_matrix = MagicMock(return_value={})
    team.evaluate_options = MagicMock(return_value=[])
    team.analyze_trade_offs = MagicMock(return_value=[])
    team.formulate_decision_criteria = MagicMock(return_value={})
    team.select_best_option = MagicMock(return_value={})
    team.elaborate_details = MagicMock(return_value=[])
    team.create_implementation_plan = MagicMock(return_value=[])
    team.optimize_implementation = MagicMock(return_value={})
    team.perform_quality_assurance = MagicMock(return_value={})
    team.extract_learnings = MagicMock(return_value=[])
    team.recognize_patterns = MagicMock(return_value=[])
    team.integrate_knowledge = MagicMock(return_value={})
    team.generate_improvement_suggestions = MagicMock(return_value=[])

    mm = MagicMock(spec=MemoryManager)
    mm.retrieve_with_edrr_phase.side_effect = lambda *a, **k: {}
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=False,
    )


def test_micro_tasks_context_spawns_cycles(coordinator):
    coordinator.start_cycle({"description": "macro"})
    context = {"micro_tasks": [{"description": "m1"}, {"description": "m2"}]}
    results = coordinator.execute_current_phase(context)
    assert len(coordinator.child_cycles) == 2
    assert len(results["micro_cycle_results"]) == 2

