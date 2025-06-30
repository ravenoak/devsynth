import types
import sys
import pytest
from unittest.mock import MagicMock, patch

# Stub heavy core module before importing coordinator
core_stub = types.ModuleType('devsynth.core')

class CoreValues:
    @classmethod
    def load(cls, *args, **kwargs):
        return cls()

    def validate_report(self, report):
        return []
def check_report_for_value_conflicts(report, core_values=None):
    return []
core_stub.CoreValues = CoreValues
core_stub.check_report_for_value_conflicts = check_report_for_value_conflicts
sys.modules['devsynth.core'] = core_stub

from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase

@pytest.fixture
def coordinator():
    mem = MagicMock()
    mem.retrieve_with_edrr_phase.return_value = {}
    wsde = MagicMock()
    code = MagicMock()
    ast = MagicMock()
    prompt = MagicMock()
    doc = MagicMock()
    return EDRRCoordinator(mem, wsde, code, ast, prompt, doc)

def test_progress_to_phase_runs(coordinator):
    coordinator.task = {'description': 'demo'}
    coordinator.cycle_id = 'cid'
    with patch.object(coordinator, '_execute_expand_phase', return_value={'done': True}) as ex:
        coordinator.progress_to_phase(Phase.EXPAND)
    ex.assert_called_once_with({})
    assert coordinator.results['EXPAND'] == {'done': True}
    assert coordinator.current_phase == Phase.EXPAND


def test_execute_expand_phase(coordinator):
    coordinator.task = {'description': 'demo'}
    coordinator.cycle_id = 'cid'
    coordinator.memory_manager.retrieve_relevant_knowledge.return_value = ['k']
    coordinator.wsde_team.generate_diverse_ideas.return_value = ['idea']
    coordinator.code_analyzer.analyze_project_structure.return_value = {'f': 1}
    res = coordinator._execute_expand_phase({})
    assert res['ideas'] == ['idea']
    assert res['knowledge'] == ['k']
    assert res['code_elements'] == {'f': 1}
    coordinator.memory_manager.store_with_edrr_phase.assert_called()


def test_execute_differentiate_phase(coordinator):
    coordinator.task = {'description': 'demo'}
    coordinator.cycle_id = 'cid'
    coordinator.memory_manager.retrieve_with_edrr_phase.return_value = {'ideas': [1, 2]}
    coordinator.wsde_team.create_comparison_matrix.return_value = 'cm'
    coordinator.wsde_team.evaluate_options.return_value = 'eo'
    coordinator.wsde_team.analyze_trade_offs.return_value = 'to'
    coordinator.wsde_team.formulate_decision_criteria.return_value = 'dc'
    res = coordinator._execute_differentiate_phase({})
    assert res['comparison_matrix'] == 'cm'
    assert res['evaluated_options'] == 'eo'
    assert res['trade_offs'] == 'to'
    assert res['decision_criteria'] == 'dc'
    coordinator.memory_manager.store_with_edrr_phase.assert_called()


def test_execute_refine_phase(coordinator):
    coordinator.task = {'description': 'demo'}
    coordinator.cycle_id = 'cid'
    def ret(item_type, phase, meta):
        if item_type == 'DIFFERENTIATE_RESULTS':
            return {'evaluated_options': [1], 'decision_criteria': {}}
        return {}
    coordinator.memory_manager.retrieve_with_edrr_phase.side_effect = ret
    coordinator.wsde_team.select_best_option.return_value = 'best'
    coordinator.wsde_team.elaborate_details.return_value = 'details'
    coordinator.wsde_team.create_implementation_plan.return_value = ['p']
    coordinator.wsde_team.optimize_implementation.return_value = {'opt': True}
    coordinator.wsde_team.perform_quality_assurance.return_value = {'qa': []}
    res = coordinator._execute_refine_phase({})
    assert res['selected_option'] == 'best'
    assert res['detailed_plan'] == 'details'
    assert res['implementation_plan'] == ['p']
    assert res['optimized_plan'] == {'opt': True}
    assert res['quality_checks'] == {'qa': []}
    coordinator.memory_manager.store_with_edrr_phase.assert_called()


def test_execute_retrospect_phase(coordinator):
    coordinator.task = {'description': 'demo'}
    coordinator.cycle_id = 'cid'
    def ret(item_type, phase, meta):
        if item_type == 'EXPAND_RESULTS':
            return {'ideas': []}
        if item_type == 'DIFFERENTIATE_RESULTS':
            return {'evaluated_options': []}
        if item_type == 'REFINE_RESULTS':
            return {'implementation_plan': [], 'quality_checks': {}}
        return {}
    coordinator.memory_manager.retrieve_with_edrr_phase.side_effect = ret
    coordinator.memory_manager.retrieve_historical_patterns.return_value = []
    coordinator.wsde_team.extract_learnings.return_value = ['l']
    coordinator.wsde_team.recognize_patterns.return_value = ['p']
    coordinator.wsde_team.integrate_knowledge.return_value = {'ik': True}
    coordinator.wsde_team.generate_improvement_suggestions.return_value = ['s']
    res = coordinator._execute_retrospect_phase({})
    assert res['learnings'] == ['l']
    assert res['patterns'] == ['p']
    assert res['integrated_knowledge'] == {'ik': True}
    assert res['improvement_suggestions'] == ['s']
    assert 'final_report' in res
    coordinator.memory_manager.store_with_edrr_phase.assert_called()
