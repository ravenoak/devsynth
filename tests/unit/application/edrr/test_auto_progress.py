import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.methodology.base import Phase

@pytest.fixture
def coordinator():
    mm = MagicMock(spec=MemoryManager)
    wsde = MagicMock(spec=WSDETeam)
    wsde.elaborate_details = MagicMock(return_value=None)
    ca = MagicMock(spec=CodeAnalyzer)
    ast = MagicMock(spec=AstTransformer)
    pm = MagicMock(spec=PromptManager)
    dm = MagicMock(spec=DocumentationManager)
    coord = EDRRCoordinator(memory_manager=mm, wsde_team=wsde, code_analyzer=ca, ast_transformer=ast, prompt_manager=pm, documentation_manager=dm)
    coord.auto_phase_transitions = True
    coord.current_phase = Phase.EXPAND
    return coord

@pytest.mark.medium
def test_maybe_auto_progress_loops_until_none_succeeds(coordinator):
    """Test that maybe auto progress loops until none succeeds.

ReqID: N/A"""
    with patch.object(coordinator, '_decide_next_phase', side_effect=[Phase.DIFFERENTIATE, None]) as decide, patch.object(coordinator, 'progress_to_phase') as prog:
        coordinator._maybe_auto_progress()
    prog.assert_called_once_with(Phase.DIFFERENTIATE)
    assert decide.call_count == 2

@pytest.mark.medium
def test_maybe_auto_progress_disabled_succeeds(coordinator):
    """Test that maybe auto progress disabled succeeds.

ReqID: N/A"""
    coordinator.auto_phase_transitions = False
    with patch.object(coordinator, '_decide_next_phase') as decide:
        coordinator._maybe_auto_progress()
    decide.assert_not_called()