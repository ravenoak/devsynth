"""
Unit tests for the enhanced recursion features in the EDRR Framework.

This module tests the enhanced termination conditions, result aggregation,
and recursion effectiveness metrics in the EDRRCoordinator.
"""
import copy
import json
from unittest.mock import MagicMock, patch
import pytest
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.methodology.base import Phase


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for the EDRRCoordinator."""
    memory_manager = MagicMock()
    wsde_team = MagicMock()
    code_analyzer = MagicMock()
    ast_transformer = MagicMock()
    prompt_manager = MagicMock()
    documentation_manager = MagicMock()
    return {'memory_manager': memory_manager, 'wsde_team': wsde_team,
        'code_analyzer': code_analyzer, 'ast_transformer': ast_transformer,
        'prompt_manager': prompt_manager, 'documentation_manager':
        documentation_manager}


@pytest.fixture
def coordinator(mock_dependencies):
    """Create an EDRRCoordinator instance for testing."""
    coordinator = EDRRCoordinator(memory_manager=mock_dependencies[
        'memory_manager'], wsde_team=mock_dependencies['wsde_team'],
        code_analyzer=mock_dependencies['code_analyzer'], ast_transformer=
        mock_dependencies['ast_transformer'], prompt_manager=
        mock_dependencies['prompt_manager'], documentation_manager=
        mock_dependencies['documentation_manager'], enable_enhanced_logging
        =True)
    coordinator.config = {'edrr': {'recursion': {'thresholds': {
        'granularity': 0.25, 'cost_benefit': 0.6, 'quality': 0.85,
        'resource': 0.75, 'complexity': 0.8, 'convergence': 0.9,
        'diminishing_returns': 0.2}}, 'aggregation': {'merge_similar': True,
        'prioritize_by_quality': True, 'handle_conflicts': True}}}
    return coordinator


class TestTerminationConditions:
    """Test the enhanced termination conditions for recursive EDRR cycles.

ReqID: N/A"""

    def test_human_override_terminate_succeeds(self, coordinator):
        """Test that human override to terminate works.

ReqID: N/A"""
        task = {'human_override': 'terminate'}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'human override'

    def test_human_override_continue_succeeds(self, coordinator):
        """Test that human override to continue works.

ReqID: N/A"""
        task = {'human_override': 'continue'}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_granularity_threshold_succeeds(self, coordinator):
        """Test that granularity threshold works.

ReqID: N/A"""
        task = {'granularity_score': 0.2}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'granularity threshold'
        task = {'granularity_score': 0.3}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_cost_benefit_analysis_succeeds(self, coordinator):
        """Test that cost-benefit analysis works.

ReqID: N/A"""
        task = {'cost_score': 0.7, 'benefit_score': 0.5}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'cost-benefit analysis'
        task = {'cost_score': 0.3, 'benefit_score': 0.5}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None
        task = {'cost_score': 0.5, 'benefit_score': 0}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'cost-benefit analysis'

    def test_quality_threshold_succeeds(self, coordinator):
        """Test that quality threshold works.

ReqID: N/A"""
        task = {'quality_score': 0.9}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'quality threshold'
        task = {'quality_score': 0.8}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_resource_limit_succeeds(self, coordinator):
        """Test that resource limit works.

ReqID: N/A"""
        task = {'resource_usage': 0.8}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'resource limit'
        task = {'resource_usage': 0.7}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_complexity_threshold_succeeds(self, coordinator):
        """Test that complexity threshold works.

ReqID: N/A"""
        task = {'complexity_score': 0.85}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'complexity threshold'
        task = {'complexity_score': 0.75}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_convergence_threshold_succeeds(self, coordinator):
        """Test that convergence threshold works.

ReqID: N/A"""
        task = {'convergence_score': 0.95}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'convergence threshold'
        task = {'convergence_score': 0.85}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_diminishing_returns(self, coordinator):
        """Test that diminishing returns threshold works.

ReqID: N/A"""
        task = {'improvement_rate': 0.15}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'diminishing returns'
        task = {'improvement_rate': 0.25}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_parent_phase_compatibility_succeeds(self, coordinator):
        """Test that parent phase compatibility works.

ReqID: N/A"""
        coordinator.parent_phase = Phase.RETROSPECT
        coordinator.recursion_depth = 1
        task = {}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'parent phase compatibility'
        coordinator.parent_phase = Phase.EXPAND
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None

    def test_historical_effectiveness_succeeds(self, coordinator,
        mock_dependencies):
        """Test that historical effectiveness check works.

ReqID: N/A"""
        patterns = [{'task_type': 'test', 'recursion_effectiveness': 0.3}]
        mock_dependencies['memory_manager'
            ].retrieve_historical_patterns.return_value = patterns
        task = {'type': 'test'}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is True
        assert reason == 'historical ineffectiveness'
        task = {'type': 'other'}
        result, reason = coordinator.should_terminate_recursion(task)
        assert result is False
        assert reason is None


class TestResultAggregation:
    """Test the enhanced result aggregation from micro cycles.

ReqID: N/A"""

    def test_process_phase_results_merge_similar_has_expected(self, coordinator
        ):
        """Test that similar results are merged in phase results.

ReqID: N/A"""
        phase_results = {'micro_cycle_results': {'cycle1': {'type':
            'analysis', 'description': 'Analysis of code', 'findings': [
            'Issue 1', 'Issue 2']}, 'cycle2': {'type': 'analysis',
            'description': 'Analysis of code', 'findings': ['Issue 2',
            'Issue 3']}}}
        processed = coordinator._process_phase_results(phase_results, Phase
            .EXPAND)
        assert 'micro_cycle_results' in processed
        all_findings = set()
        for key, result in processed['micro_cycle_results'].items():
            if isinstance(result, dict) and 'findings' in result:
                all_findings.update(result['findings'])
        assert 'Issue 1' in all_findings, 'Issue 1 is missing from the processed results'
        assert 'Issue 2' in all_findings, 'Issue 2 is missing from the processed results'
        assert 'Issue 3' in all_findings, 'Issue 3 is missing from the processed results'
        assert 'type' in processed['micro_cycle_results']['cycle1'
            ], 'type is missing from cycle1'
        assert 'description' in processed['micro_cycle_results']['cycle1'
            ], 'description is missing from cycle1'
        assert 'findings' in processed['micro_cycle_results']['cycle1'
            ], 'findings is missing from cycle1'
        assert processed['micro_cycle_results']['cycle1']['type'
            ] == 'analysis', 'type is incorrect in cycle1'
        assert processed['micro_cycle_results']['cycle1']['description'
            ] == 'Analysis of code', 'description is incorrect in cycle1'

    def test_process_phase_results_prioritize_by_quality_has_expected(self,
        coordinator):
        """Test that results are prioritized by quality in phase results.

ReqID: N/A"""
        phase_results = {'micro_cycle_results': {'cycle1': {'type':
            'analysis', 'description': 'Low quality analysis',
            'quality_score': 0.3}, 'cycle2': {'type': 'analysis',
            'description': 'High quality analysis', 'quality_score': 0.8}}}
        processed = coordinator._process_phase_results(phase_results, Phase
            .EXPAND)
        assert 'top_results' in processed
        assert len(processed['top_results']) == 2
        top_key = next(iter(processed['top_results']))
        assert processed['top_results'][top_key]['quality_score'] == 0.8

    def test_process_phase_results_handle_conflicts_has_expected(self,
        coordinator):
        """Test that conflicts are handled in phase results.

ReqID: N/A"""
        phase_results = {'micro_cycle_results': {'cycle1': {'type':
            'implementation', 'approach': 'Use a database', 'quality_score':
            0.7}, 'cycle2': {'type': 'implementation', 'approach':
            'Use a file system', 'quality_score': 0.6}}}
        processed = coordinator._process_phase_results(phase_results, Phase
            .REFINE)
        assert 'resolved_conflicts' in processed
        assert 'approach' in processed['resolved_conflicts']
        resolved = processed['resolved_conflicts']['approach']
        assert resolved['primary_approach']['quality_score'] == 0.7
        assert len(resolved['alternative_approaches']) == 1

    def test_merge_cycle_results_succeeds(self, coordinator):
        """Test merging results from multiple cycles.

ReqID: N/A"""
        cycle1 = MagicMock()
        cycle1.cycle_id = 'cycle1'
        cycle1.results = {'EXPAND': {'ideas': ['Idea 1', 'Idea 2']}}
        cycle2 = MagicMock()
        cycle2.cycle_id = 'cycle2'
        cycle2.results = {'EXPAND': {'ideas': ['Idea 2', 'Idea 3']}}
        merged = coordinator._merge_cycle_results([cycle1, cycle2])
        assert len(merged) == 1
        merged_key = next(iter(merged))
        merged_result = merged[merged_key]
        assert 'merged_from' in merged_result
        assert 'cycle1' in merged_result['merged_from']
        assert 'cycle2' in merged_result['merged_from']
        assert 'ideas' in merged_result
        assert set(merged_result['ideas']) == {'Idea 1', 'Idea 2', 'Idea 3'}

    def test_calculate_similarity_key_succeeds(self, coordinator):
        """Test calculating similarity keys for results.

ReqID: N/A"""
        result1 = {'type': 'analysis', 'description': 'Analysis of code',
            'findings': ['Issue 1', 'Issue 2']}
        key1 = coordinator._calculate_similarity_key(result1)
        result2 = {'type': 'analysis', 'description': 'Analysis of code',
            'findings': ['Issue 2', 'Issue 3']}
        key2 = coordinator._calculate_similarity_key(result2)
        result3 = {'type': 'implementation', 'description':
            'Implementation of feature', 'code': 'def foo(): pass'}
        key3 = coordinator._calculate_similarity_key(result3)
        assert key1 == key2
        assert key1 != key3

    def test_merge_similar_results_succeeds(self, coordinator):
        """Test merging similar results.

ReqID: N/A"""
        result1 = {'type': 'analysis', 'description': 'Analysis of code',
            'findings': ['Issue 1', 'Issue 2']}
        result2 = {'type': 'analysis', 'description': 'Analysis of code',
            'findings': ['Issue 2', 'Issue 3']}
        merged = coordinator._merge_similar_results([('cycle1', result1), (
            'cycle2', result2)])
        assert 'merged_from' in merged
        assert 'cycle1' in merged['merged_from']
        assert 'cycle2' in merged['merged_from']
        assert 'findings' in merged
        assert set(merged['findings']) == {'Issue 1', 'Issue 2', 'Issue 3'}

    def test_merge_dicts_succeeds(self, coordinator):
        """Test merging dictionaries.

ReqID: N/A"""
        dict1 = {'key1': 'value1', 'key2': ['item1', 'item2'], 'key3': {
            'subkey1': 'subvalue1'}}
        dict2 = {'key2': ['item2', 'item3'], 'key3': {'subkey2':
            'subvalue2'}, 'key4': 'value4'}
        merged = coordinator._merge_dicts(dict1, dict2)
        assert merged['key1'] == 'value1'
        assert set(merged['key2']) == {'item1', 'item2', 'item3'}
        assert merged['key3']['subkey1'] == 'subvalue1'
        assert merged['key3']['subkey2'] == 'subvalue2'
        assert merged['key4'] == 'value4'

    def test_merge_lists_succeeds(self, coordinator):
        """Test merging lists.

ReqID: N/A"""
        list1 = ['item1', 'item2', 'item3']
        list2 = ['item2', 'item3', 'item4']
        merged = coordinator._merge_lists(list1, list2)
        assert set(merged) == {'item1', 'item2', 'item3', 'item4'}

    def test_are_items_similar_succeeds(self, coordinator):
        """Test checking if items are similar.

ReqID: N/A"""
        item1 = {'id': '1', 'type': 'analysis', 'description':
            'Analysis of code', 'extra': 'value1'}
        item2 = {'id': '1', 'type': 'analysis', 'description':
            'Analysis of code', 'extra': 'value2'}
        assert coordinator._are_items_similar(item1, item2) is True
        item3 = {'id': '2', 'type': 'implementation', 'description':
            'Implementation of feature', 'extra': 'value3'}
        assert coordinator._are_items_similar(item1, item3) is False
        assert coordinator._are_items_similar('string1', 'string1') is True
        assert coordinator._are_items_similar('string1', 'string2') is False

    def test_calculate_quality_score_succeeds(self, coordinator):
        """Test calculating quality scores for results.

ReqID: N/A"""
        result1 = {'description': 'High quality analysis', 'approach':
            'Sophisticated approach', 'implementation':
            'Detailed implementation', 'analysis': 'Thorough analysis',
            'solution': 'Elegant solution'}
        score1 = coordinator._calculate_quality_score(result1)
        result2 = {'description': 'Low quality analysis'}
        score2 = coordinator._calculate_quality_score(result2)
        result3 = {'description': 'Medium quality analysis',
            'quality_score': 0.6}
        score3 = coordinator._calculate_quality_score(result3)
        result4 = {'description': 'Failed analysis', 'error':
            'Something went wrong'}
        score4 = coordinator._calculate_quality_score(result4)
        assert score1 > 0.7
        assert score2 < 0.6
        assert 0.55 < score3 < 0.65
        assert score4 < 0.4

    def test_identify_conflicts_succeeds(self, coordinator):
        """Test identifying conflicts between results.

ReqID: N/A"""
        results = {'cycle1': {'approach': 'Use a database', 'quality_score':
            0.7}, 'cycle2': {'approach': 'Use a file system',
            'quality_score': 0.6}, 'cycle3': {'approach': 'Use a database',
            'quality_score': 0.5}}
        conflicts = coordinator._identify_conflicts(results)
        assert 'approach' in conflicts
        assert len(conflicts['approach']) == 2
        db_group = None
        fs_group = None
        for approach_key, group in conflicts['approach']:
            if 'database' in approach_key:
                db_group = group
            elif 'file system' in approach_key:
                fs_group = group
        assert db_group is not None
        assert fs_group is not None
        assert len(db_group) == 2
        assert len(fs_group) == 1

    def test_resolve_conflict_succeeds(self, coordinator):
        """Test resolving conflicts between results.

ReqID: N/A"""
        conflict = [('database', [('cycle1', {'approach': 'Use a database',
            'quality_score': 0.7}), ('cycle3', {'approach':
            'Use a database', 'quality_score': 0.5})]), ('file_system', [(
            'cycle2', {'approach': 'Use a file system', 'quality_score': 
            0.6})])]
        resolved, _ = coordinator._resolve_conflict(conflict)
        assert 'primary_approach' in resolved
        assert 'alternative_approaches' in resolved
        assert 'resolution_method' in resolved
        assert 'resolution_notes' in resolved
        assert resolved['primary_approach']['cycle_id'] == 'cycle1'
        assert resolved['primary_approach']['quality_score'] == 0.7
        assert len(resolved['alternative_approaches']) == 2
        assert resolved['resolution_method'] == 'quality_based_selection'


class TestRecursionMetrics:
    """Test the metrics for recursion effectiveness.

ReqID: N/A"""

    def test_calculate_recursion_metrics_no_children_succeeds(self, coordinator
        ):
        """Test calculating recursion metrics with no child cycles.

ReqID: N/A"""
        metrics = coordinator._calculate_recursion_metrics()
        assert metrics['total_cycles'] == 1
        assert metrics['max_depth'] == 0
        assert metrics['cycles_by_depth'] == {(0): 1}
        assert metrics['effectiveness_score'] == 0.0
        assert metrics['improvement_rate'] == 0.0
        assert metrics['convergence_rate'] == 0.0

    def test_calculate_recursion_metrics_with_children_succeeds(self,
        coordinator):
        """Test calculating recursion metrics with child cycles.

ReqID: N/A"""
        child1 = MagicMock()
        child1.recursion_depth = 1
        child1.results = {'AGGREGATED': {'quality_score': 0.7}}
        child2 = MagicMock()
        child2.recursion_depth = 1
        child2.results = {'AGGREGATED': {'quality_score': 0.9}}
        child3 = MagicMock()
        child3.recursion_depth = 2
        child3.results = {'AGGREGATED': {'quality_score': 0.8}}
        coordinator.child_cycles = [child1, child2, child3]
        metrics = coordinator._calculate_recursion_metrics()
        assert metrics['total_cycles'] == 4
        assert metrics['max_depth'] == 0
        assert metrics['cycles_by_depth'] == {(0): 1, (1): 2, (2): 1}
        assert metrics['improvement_rate'] == pytest.approx(0.8)
        assert 0.7 < metrics['convergence_rate'] < 0.95
        assert 0.5 < metrics['effectiveness_score'] < 0.9

    def test_aggregate_results_with_metrics_contains_expected(self, coordinator
        ):
        """Test that aggregating results includes recursion metrics.

ReqID: N/A"""
        child = MagicMock()
        child.recursion_depth = 1
        child.parent_phase = Phase.EXPAND
        child.results = {'EXPAND': {'ideas': ['Idea 1', 'Idea 2']}}
        coordinator.child_cycles = [child]
        coordinator.results = {'EXPAND': {'ideas': ['Parent Idea 1',
            'Parent Idea 2']}}
        coordinator.performance_metrics = {'EXPAND': {'duration': 10},
            'DIFFERENTIATE': {'duration': 20}}
        coordinator._aggregate_results()
        assert 'TOTAL' in coordinator.performance_metrics
        assert 'recursion_metrics' in coordinator.performance_metrics['TOTAL']
        metrics = coordinator.performance_metrics['TOTAL']['recursion_metrics']
        assert 'total_cycles' in metrics
        assert 'max_depth' in metrics
        assert 'cycles_by_depth' in metrics
        assert 'effectiveness_score' in metrics
        assert 'improvement_rate' in metrics
        assert 'convergence_rate' in metrics
