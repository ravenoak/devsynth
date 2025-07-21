"""
Integration tests for GraphMemoryAdapter and EDRRCoordinator.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock
from devsynth.methodology.base import Phase
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.edrr.coordinator import EDRRCoordinator
from devsynth.domain.models.memory import MemoryItem, MemoryType


class TestGraphMemoryEDRRIntegration:
    """Integration tests for GraphMemoryAdapter and EDRRCoordinator.

ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def graph_adapter(self, temp_dir):
        """Create a GraphMemoryAdapter instance for testing."""
        return GraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for the EDRRCoordinator."""
        wsde_team = MagicMock()
        code_analyzer = MagicMock()
        ast_transformer = MagicMock()
        prompt_manager = MagicMock()
        documentation_manager = MagicMock()
        approaches = [{'id': 'approach-1', 'description': 'First approach',
            'code': 'def approach1(): pass'}, {'id': 'approach-2',
            'description': 'Second approach', 'code': 'def approach2(): pass'}]
        wsde_team.brainstorm_approaches.return_value = approaches
        evaluation = {'selected_approach': approaches[0], 'rationale':
            'This approach is better'}
        wsde_team.evaluate_approaches.return_value = evaluation
        implementation = {'code':
            "def approach1_improved(): return 'Hello, World!'",
            'description': 'Improved implementation'}
        wsde_team.implement_approach.return_value = implementation
        implementation_evaluation = {'quality': 'good', 'issues': [],
            'suggestions': []}
        wsde_team.evaluate_implementation.return_value = (
            implementation_evaluation)
        return {'wsde_team': wsde_team, 'code_analyzer': code_analyzer,
            'ast_transformer': ast_transformer, 'prompt_manager':
            prompt_manager, 'documentation_manager': documentation_manager}

    @pytest.fixture
    def coordinator(self, graph_adapter, mock_dependencies):
        """Create an EDRRCoordinator instance with a GraphMemoryAdapter for testing."""
        config = {'edrr': {'max_recursion_depth': 3, 'phase_transition': {
            'auto': False}}, 'features': {'automatic_phase_transitions': False}
            }
        return EDRRCoordinator(memory_manager=graph_adapter, wsde_team=
            mock_dependencies['wsde_team'], code_analyzer=mock_dependencies
            ['code_analyzer'], ast_transformer=mock_dependencies[
            'ast_transformer'], prompt_manager=mock_dependencies[
            'prompt_manager'], documentation_manager=mock_dependencies[
            'documentation_manager'], enable_enhanced_logging=True, config=
            config)

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return {'id': 'task-123', 'description': 'Implement a feature',
            'code': 'def example(): pass'}

    def test_edrr_cycle_with_graph_memory_succeeds(self, coordinator,
        graph_adapter, sample_task, mock_dependencies):
        """Test a complete EDRR cycle with GraphMemoryAdapter integration.

ReqID: N/A"""
        coordinator.start_cycle(sample_task)
        task_items = graph_adapter.search({'type': MemoryType.TASK_HISTORY.
            value})
        if not task_items:
            task_items = graph_adapter.search({'type': 'TASK'})
        assert len(task_items) > 0
        print(f'Task item content: {task_items[0].content}')
        print(f'Task item content type: {type(task_items[0].content)}')
        if hasattr(task_items[0], 'metadata'):
            print(f'Task item metadata: {task_items[0].metadata}')
        if isinstance(task_items[0].content, str):
            if task_items[0].content.strip().startswith('{') and task_items[0
                ].content.strip().endswith('}'):
                import json
                try:
                    content_dict = json.loads(task_items[0].content)
                    assert content_dict['id'] == sample_task['id']
                    assert content_dict['description'] == sample_task[
                        'description']
                except (json.JSONDecodeError, KeyError) as e:
                    print(f'Failed to parse content as JSON: {e}')
                    assert sample_task['id'] in task_items[0].content
                    assert sample_task['description'] in task_items[0].content
            else:
                assert sample_task['id'] in task_items[0].content
                assert sample_task['description'] in task_items[0].content
        else:
            assert task_items[0].content['id'] == sample_task['id']
            assert task_items[0].content['description'] == sample_task[
                'description']
        assert coordinator.cycle_id is not None
        assert coordinator.task is not None
        assert coordinator.task['id'] == sample_task['id']
        assert coordinator.task['description'] == sample_task['description']
        assert coordinator.current_phase == Phase.EXPAND
        if coordinator._enable_enhanced_logging:
            traces = coordinator.get_execution_traces()
            assert 'cycle_id' in traces
            history = coordinator.get_execution_history()
            assert len(history) > 0

    def test_memory_volatility_with_edrr_succeeds(self, coordinator,
        graph_adapter, sample_task):
        """Test memory volatility controls with EDRR integration.

ReqID: N/A"""
        coordinator.start_cycle(sample_task)
        graph_adapter.add_memory_volatility(decay_rate=0.3, threshold=0.5,
            advanced_controls=True)
        task_items = graph_adapter.search({'type': MemoryType.TASK_HISTORY.
            value})
        if not task_items:
            task_items = graph_adapter.search({'type': 'TASK'})
        assert len(task_items) > 0
        for i in range(5):
            item = MemoryItem(id='', content=f'Test item {i}', memory_type=
                MemoryType.CODE, metadata={'edrr_phase': Phase.EXPAND.name,
                'cycle_id': coordinator.cycle_id, 'confidence': 0.4,
                'last_accessed': (datetime.now() - timedelta(days=10)).
                isoformat()})
            graph_adapter.store(item)
        volatile_items = graph_adapter.apply_memory_decay(advanced_decay=True)
        print(f'Volatile items: {volatile_items}')
        task_items = graph_adapter.search({'type': MemoryType.TASK_HISTORY.
            value})
        if not task_items:
            task_items = graph_adapter.search({'type': 'TASK'})
        assert len(task_items) > 0

    def test_query_edrr_phases_from_graph_has_expected(self, coordinator,
        graph_adapter, sample_task):
        """Test querying EDRR phases from the graph memory.

ReqID: N/A"""
        coordinator.start_cycle(sample_task)
        expand_items = graph_adapter.search({'edrr_phase': Phase.EXPAND.name})
        assert len(expand_items) > 0
        for item in expand_items:
            assert item.metadata.get('edrr_phase') == Phase.EXPAND.name

    def test_relationships_across_edrr_phases_has_expected(self,
        coordinator, graph_adapter, sample_task):
        """Test relationships between items across EDRR phases.

ReqID: N/A"""
        coordinator.start_cycle(sample_task)
        expand_item = MemoryItem(id='expand-item', content=
            'Expand phase item', memory_type=MemoryType.CODE, metadata={
            'edrr_phase': 'EXPAND', 'cycle_id': coordinator.cycle_id})
        graph_adapter.store(expand_item)
        differentiate_item = MemoryItem(id='differentiate-item', content=
            'Differentiate phase item', memory_type=MemoryType.CODE,
            metadata={'edrr_phase': 'DIFFERENTIATE', 'cycle_id':
            coordinator.cycle_id, 'related_to': 'expand-item'})
        graph_adapter.store(differentiate_item)
        refine_item = MemoryItem(id='refine-item', content=
            'Refine phase item', memory_type=MemoryType.CODE, metadata={
            'edrr_phase': 'REFINE', 'cycle_id': coordinator.cycle_id,
            'related_to': 'differentiate-item'})
        graph_adapter.store(refine_item)
        retrospect_item = MemoryItem(id='retrospect-item', content=
            'Retrospect phase item', memory_type=MemoryType.CODE, metadata=
            {'edrr_phase': 'RETROSPECT', 'cycle_id': coordinator.cycle_id,
            'related_to': 'refine-item'})
        graph_adapter.store(retrospect_item)
        related_to_expand = graph_adapter.query_related_items('expand-item')
        assert len(related_to_expand) == 1
        assert related_to_expand[0].id == 'differentiate-item'
        relationships = graph_adapter.get_all_relationships()
        assert 'expand-item' in relationships
        assert 'differentiate-item' in relationships
        assert 'refine-item' in relationships
        assert 'retrospect-item' in relationships
