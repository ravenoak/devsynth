import pytest
from unittest.mock import MagicMock, patch
from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.application.code_analysis.ast_transformer import AstTransformer
from devsynth.application.prompts.prompt_manager import PromptManager
from devsynth.application.documentation.documentation_manager import DocumentationManager
from devsynth.methodology.base import Phase

@pytest.fixture
def coordinator():
    mm = MagicMock(spec=MemoryManager)
    mm.store_with_edrr_phase.return_value = 'id'
    mm.retrieve_with_edrr_phase.return_value = {}
    mm.retrieve_historical_patterns.return_value = []
    mm.retrieve_relevant_knowledge.return_value = []
    team = MagicMock()
    team.process.return_value = {'quality_score': 0.6}
    team.apply_enhanced_dialectical_reasoning.side_effect = lambda task, res: res
    coord = EDRRCoordinator(memory_manager=mm, wsde_team=team, code_analyzer=MagicMock(spec=CodeAnalyzer), ast_transformer=MagicMock(spec=AstTransformer), prompt_manager=MagicMock(spec=PromptManager), documentation_manager=MagicMock(spec=DocumentationManager), enable_enhanced_logging=True)
    coord.config = {'edrr': {'micro_cycles': {'max_iterations': 2, 'quality_threshold': 0.8}}}
    return coord

@pytest.mark.medium
def test_micro_cycle_iterations_until_threshold(coordinator):
    coordinator.current_phase = Phase.EXPAND
    coordinator.task = {'description': 'task'}
    coordinator.cycle_id = 'cid'
    with patch.object(coordinator, '_execute_expand_phase', return_value={'quality_score': 0.5}):
        coordinator.wsde_team.process.side_effect = [{'quality_score': 0.6}, {'quality_score': 0.9}]
        results = coordinator.execute_current_phase()
    assert coordinator.wsde_team.process.call_count == 2
    phase_results = coordinator.results[Phase.EXPAND.name]
    assert len(phase_results['micro_cycle_iterations']) == 2
    assert phase_results['aggregated_results']['quality_score'] == 0.9
    assert results['quality_score'] == 0.9

@pytest.mark.medium
def test_phase_execution_recovery_hook(coordinator):
    coordinator.current_phase = Phase.EXPAND
    coordinator.task = {'description': 'task'}
    coordinator.cycle_id = 'cid'
    with patch.object(coordinator, '_execute_expand_phase', side_effect=RuntimeError('boom')):
        with patch.object(coordinator, '_attempt_recovery', return_value={'recovered': True}) as rec:
            results = coordinator.execute_current_phase()
    rec.assert_called_once()
    assert results.get('recovery_info')

@pytest.mark.medium
def test_micro_cycle_respects_max_iterations(coordinator):
    coordinator.config['edrr']['micro_cycles']['max_iterations'] = 1
    coordinator.current_phase = Phase.EXPAND
    coordinator.task = {'description': 'task'}
    coordinator.cycle_id = 'cid'
    with patch.object(coordinator, '_execute_expand_phase', return_value={'quality_score': 0.1}):
        coordinator.wsde_team.process.return_value = {'quality_score': 0.2}
        results = coordinator.execute_current_phase()
    assert coordinator.wsde_team.process.call_count == 1
    phase_results = coordinator.results[Phase.EXPAND.name]
    assert len(phase_results['micro_cycle_iterations']) == 1
    assert phase_results['aggregated_results']['quality_score'] == 0.2
    assert results['quality_score'] == 0.2