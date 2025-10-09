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
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase


class ExpertAgent:

    def __init__(self, name, expertise):
        self.name = name
        self.expertise = expertise
        self.current_role = None


@pytest.fixture
def coordinator():
    team = WSDETeam(name="TestEdrrDynamicRolesTeam")
    team.add_agents(
        [
            ExpertAgent("expand", ["expand"]),
            ExpertAgent("diff", ["differentiate"]),
            ExpertAgent("refine", ["refine"]),
        ]
    )
    mm = MagicMock(spec=MemoryManager)
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


@pytest.mark.slow
def test_dynamic_role_assignment_across_phases_succeeds(coordinator):
    """Test that dynamic role assignment across phases succeeds.

    ReqID: N/A"""
    task = {"description": "demo"}
    coordinator.start_cycle(task)
    assert coordinator.wsde_team.get_primus().name == "expand"
    coordinator.progress_to_next_phase()
    assert coordinator.wsde_team.get_primus().name == "diff"
    coordinator.progress_to_next_phase()
    assert coordinator.wsde_team.get_primus().name == "refine"
