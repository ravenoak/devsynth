import pytest
from unittest.mock import patch, MagicMock
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
    memory_manager = MagicMock(spec=MemoryManager)
    memory_manager.store_with_edrr_phase.return_value = None
    memory_manager.retrieve_with_edrr_phase.return_value = {}
    memory_manager.retrieve_historical_patterns.return_value = []
    memory_manager.retrieve_relevant_knowledge.return_value = []
    wsde_team = MagicMock(spec=WSDETeam)
    wsde_team.generate_diverse_ideas.return_value = []
    wsde_team.create_comparison_matrix.return_value = {}
    wsde_team.evaluate_options.return_value = []
    wsde_team.analyze_trade_offs.return_value = []
    wsde_team.formulate_decision_criteria.return_value = {}
    wsde_team.select_best_option.return_value = {}
    wsde_team.elaborate_details.return_value = []
    wsde_team.create_implementation_plan.return_value = []
    wsde_team.optimize_implementation.return_value = {}
    wsde_team.perform_quality_assurance.return_value = {}
    wsde_team.extract_learnings.return_value = []
    wsde_team.recognize_patterns.return_value = []
    wsde_team.integrate_knowledge.return_value = {}
    wsde_team.generate_improvement_suggestions.return_value = []
    wsde_team.get_role_map.return_value = {}
    wsde_team.get_primus.return_value = 'primus'
    code_analyzer = MagicMock(spec=CodeAnalyzer)
    code_analyzer.analyze_project_structure.return_value = []
    ast_transformer = MagicMock(spec=AstTransformer)
    prompt_manager = MagicMock(spec=PromptManager)
    documentation_manager = MagicMock(spec=DocumentationManager)
    return EDRRCoordinator(memory_manager=memory_manager, wsde_team=
        wsde_team, code_analyzer=code_analyzer, ast_transformer=
        ast_transformer, prompt_manager=prompt_manager,
        documentation_manager=documentation_manager)


def test_auto_phase_progression_succeeds(coordinator):
    """Test that auto phase progression succeeds.

ReqID: N/A"""
    with patch.object(coordinator, '_execute_expand_phase', return_value={
        'phase_complete': True}), patch.object(coordinator,
        '_execute_differentiate_phase', return_value={'phase_complete': True}
        ), patch.object(coordinator, '_execute_refine_phase', return_value=
        {'phase_complete': True}), patch.object(coordinator,
        '_execute_retrospect_phase', return_value={'phase_complete': True}):
        coordinator.start_cycle({'description': 'Task'})
        assert coordinator.current_phase == Phase.RETROSPECT
        for phase in Phase:
            assert phase.name in coordinator.results


def test_micro_cycle_result_aggregation_succeeds(coordinator):
    """Test that micro cycle result aggregation succeeds.

ReqID: N/A"""
    with patch.object(coordinator, '_execute_expand_phase', return_value={
        'phase_complete': True}):
        coordinator.start_cycle({'description': 'Macro'})
        micro_cycle = coordinator.create_micro_cycle({'description':
            'Micro'}, Phase.EXPAND)
        stored = coordinator.results[Phase.EXPAND.name]['micro_cycle_results'][
            micro_cycle.cycle_id]
        assert stored['task'] == {'description': 'Micro'}
        for key, value in micro_cycle.results.items():
            assert stored[key] == value


def test_result_aggregation_after_full_cycle_has_expected(coordinator):
    """All phase results should be aggregated after auto progression.

ReqID: N/A"""
    with patch.object(coordinator, '_execute_expand_phase', return_value={
        'expand': True, 'phase_complete': True}), patch.object(coordinator,
        '_execute_differentiate_phase', return_value={'differentiate': True,
        'phase_complete': True}), patch.object(coordinator,
        '_execute_refine_phase', return_value={'refine': True,
        'phase_complete': True}), patch.object(coordinator,
        '_execute_retrospect_phase', return_value={'retrospect': True,
        'phase_complete': True}):
        coordinator.start_cycle({'description': 'Task'})
    aggregated = coordinator.results.get('AGGREGATED', {})
    assert aggregated['expand']['expand'] is True
    assert aggregated['differentiate']['differentiate'] is True
    assert aggregated['refine']['refine'] is True
    assert aggregated['retrospect']['retrospect'] is True
