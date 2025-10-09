from unittest.mock import MagicMock

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:

    def __init__(self, name):
        self.name = name
        self.current_role = None
        self.expertise = []

    def process(self, task):
        return {"processed_by": self.name, "role": self.current_role}


@pytest.fixture
def wsde_team():
    team = WSDETeam(name="TestEdrrPrimusRotationTeam")
    for i in range(4):
        team.add_agent(SimpleAgent(f"agent{i + 1}"))
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
    return team


@pytest.fixture
def coordinator(wsde_team):
    mm = MagicMock()

    def retrieve_with_phase(item_type, phase, metadata):
        if item_type == MemoryType.EXPAND_RESULTS:
            return {"ideas": []}
        if item_type == MemoryType.DIFFERENTIATE_RESULTS:
            return {"evaluated_options": [], "decision_criteria": {}}
        if item_type == MemoryType.REFINE_RESULTS:
            return {"implementation_plan": [], "quality_checks": {}}
        return {}

    mm.retrieve_with_edrr_phase.side_effect = retrieve_with_phase
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock()
    analyzer.analyze_project_structure.return_value = []
    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde_team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(),
        prompt_manager=MagicMock(),
        documentation_manager=MagicMock(),
        enable_enhanced_logging=False,
    )


@pytest.mark.slow
def test_full_cycle_rotating_primus_succeeds(coordinator, wsde_team):
    """Test that full cycle rotating primus succeeds.

    ReqID: N/A"""
    task = {"description": "demo"}
    coordinator.start_cycle(task)
    primus_sequence = [wsde_team.get_primus().name]
    coordinator.progress_to_phase(Phase.DIFFERENTIATE)
    primus_sequence.append(wsde_team.get_primus().name)
    coordinator.progress_to_phase(Phase.REFINE)
    primus_sequence.append(wsde_team.get_primus().name)
    coordinator.progress_to_phase(Phase.RETROSPECT)
    primus_sequence.append(wsde_team.get_primus().name)
    assert primus_sequence == ["agent1", "agent2", "agent3", "agent4"]
