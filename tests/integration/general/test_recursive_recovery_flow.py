from unittest.mock import MagicMock

import pytest

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.documentation.documentation_manager import (
    DocumentationManager,
)
from devsynth.application.edrr.edrr_coordinator_enhanced import EnhancedEDRRCoordinator
from devsynth.application.edrr.edrr_phase_transitions import MetricType
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.requirements.prompt_manager import PromptManager
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class SimpleAgent:
    def __init__(self, name):
        self.name = name
        self.expertise = []
        self.current_role = None

    def process(self, task):
        return {"processed_by": self.name}


@pytest.fixture
def enhanced_coordinator():
    team = WSDETeam(name="RecursiveRecoveryTeam")
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
    mm = MemoryManager()
    analyzer = MagicMock(spec=CodeAnalyzer)
    analyzer.analyze_project_structure.return_value = []
    coord = EnhancedEDRRCoordinator(
        memory_manager=mm,
        wsde_team=team,
        code_analyzer=analyzer,
        ast_transformer=MagicMock(spec=AstTransformer),
        prompt_manager=MagicMock(spec=PromptManager),
        documentation_manager=MagicMock(spec=DocumentationManager),
    )
    coord.start_cycle({"description": "macro"})
    return coord


@pytest.mark.medium
def test_recursive_recovery_flow(enhanced_coordinator):
    micro = enhanced_coordinator.create_micro_cycle(
        {"description": "micro"}, Phase.EXPAND
    )

    def hook(metrics):
        metrics[MetricType.QUALITY.value] = 1.0
        return {"recovered": True}

    micro.register_phase_recovery_hook(Phase.EXPAND, hook)
    micro.phase_metrics.end_phase(
        Phase.EXPAND,
        {
            MetricType.QUALITY.value: 0.2,
            MetricType.COMPLETENESS.value: 1.0,
            MetricType.CONSISTENCY.value: 1.0,
            MetricType.CONFLICTS.value: 0,
        },
    )
    micro._enhanced_maybe_auto_progress()
    assert micro.current_phase == Phase.DIFFERENTIATE
