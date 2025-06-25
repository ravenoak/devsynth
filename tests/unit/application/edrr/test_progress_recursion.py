from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager


@pytest.fixture
def coordinator():
    mm = MagicMock(spec=MemoryManager)
    mm.store_with_edrr_phase.return_value = None
    wsde = MagicMock(spec=WSDETeam)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    return EDRRCoordinator(
        memory_manager=mm,
        wsde_team=wsde,
        code_analyzer=ca,
        ast_transformer=ast,
        prompt_manager=pm,
        documentation_manager=dm,
    )


def test_progress_to_phase_auto_recursion(coordinator):
    coordinator.task = {"description": "t"}
    coordinator.cycle_id = "cid"
    coordinator.auto_phase_transitions = True
    phase_iter = iter([Phase.DIFFERENTIATE, Phase.REFINE, Phase.RETROSPECT])
    with patch.object(coordinator, "_execute_expand_phase", return_value={"phase_complete": True}) as ex, \
        patch.object(coordinator, "_execute_differentiate_phase", return_value={"phase_complete": True}) as diff, \
        patch.object(coordinator, "_execute_refine_phase", return_value={"phase_complete": True}) as ref, \
        patch.object(coordinator, "_execute_retrospect_phase", return_value={"phase_complete": True}) as ret, \
        patch.object(coordinator, "_decide_next_phase", side_effect=lambda: next(phase_iter, None)):
        coordinator.progress_to_phase(Phase.EXPAND)
    assert coordinator.current_phase == Phase.RETROSPECT
    assert ex.called and diff.called and ref.called and ret.called
