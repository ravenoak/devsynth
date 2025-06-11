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
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:
    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.current_role = None


@pytest.fixture
def coordinator():
    team = WSDETeam()
    team.add_agents(
        [
            SimpleAgent("expand", ["expand"]),
            SimpleAgent("diff", ["differentiate"]),
            SimpleAgent("refine", ["refine"]),
            SimpleAgent("retro", ["retrospect"]),
        ]
    )
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

    def retrieve_with_phase(item_type, phase, metadata):
        if item_type == "EXPAND_RESULTS":
            return {"ideas": []}
        if item_type == "DIFFERENTIATE_RESULTS":
            return {"evaluated_options": [], "decision_criteria": {}}
        if item_type == "REFINE_RESULTS":
            return {"implementation_plan": [], "quality_checks": {}}
        return {}

    mm.retrieve_with_edrr_phase.side_effect = retrieve_with_phase
    mm.retrieve_relevant_knowledge.return_value = []
    mm.retrieve_historical_patterns.return_value = []
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []

    config = {
        "edrr": {"phase_transition": {"auto": True, "timeout": 0}},
        "features": {"automatic_phase_transitions": True},
    }

    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
        enable_enhanced_logging=False,
        config=config,
    )


def test_full_cycle_auto_transition_dynamic_roles(coordinator):
    task = {"description": "demo"}
    coordinator.start_cycle(task)
    assert coordinator.current_phase == Phase.RETROSPECT
    calls = [
        c.args[2]
        for c in coordinator.memory_manager.store_with_edrr_phase.call_args_list
        if c.args[1] == "ROLE_ASSIGNMENT"
    ]
    calls = calls[-4:]
    assert calls == [
        Phase.EXPAND.value,
        Phase.DIFFERENTIATE.value,
        Phase.REFINE.value,
        Phase.RETROSPECT.value,
    ]
