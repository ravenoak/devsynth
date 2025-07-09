import unittest
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration
from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration


@pytest.mark.isolation
class TestWSDEMemoryIntegration(unittest.TestCase):
    """Test the integration between WSDE and the memory system.

    These tests need to be run in isolation due to interactions with other tests.

ReqID: N/A"""

    @classmethod
    def setUpClass(cls):
        """Set up the test class."""
        # Reset any global state that might affect the tests
        import sys
        if 'devsynth.application.agents.wsde_memory_integration' in sys.modules:
            del sys.modules['devsynth.application.agents.wsde_memory_integration']

    def setUp(self):
        """Set up the test environment."""
        # Create the mock without spec first to avoid attribute errors
        self.memory_adapter = MagicMock()
        self.memory_store = MagicMock()
        self.context_manager = MagicMock()
        self.vector_store = MagicMock()

        # Set up the return values for the methods
        self.memory_adapter.get_memory_store.return_value = self.memory_store
        self.memory_adapter.get_context_manager.return_value = self.context_manager
        self.memory_adapter.get_vector_store.return_value = self.vector_store
        self.memory_adapter.has_vector_store.return_value = True

        # Now add the spec to ensure type checking works correctly
        self.memory_adapter.__class__ = MemorySystemAdapter

        self.wsde_team = MagicMock(spec=WSDETeam)
        self.agent_memory = MagicMock(spec=AgentMemoryIntegration)

        # Create the WSDEMemoryIntegration instance with our mocks
        self.wsde_memory = WSDEMemoryIntegration(
            memory_adapter=self.memory_adapter, 
            wsde_team=self.wsde_team, 
            agent_memory=self.agent_memory
        )

        # Patch the context_manager attribute directly to ensure it's using our mock
        self.wsde_memory.context_manager = self.context_manager

    def test_store_dialectical_process_succeeds(self):
        """Test storing a dialectical process in memory.

ReqID: N/A"""
        task = {'id': 'task1', 'description': 'Test task'}
        thesis = {'id': 'thesis1', 'content': 'Thesis content'}
        antithesis = {'id': 'antithesis1', 'content': 'Antithesis content'}
        synthesis = {'id': 'synthesis1', 'content': 'Synthesis content'}
        result = self.wsde_memory.store_dialectical_process(task, thesis,
            antithesis, synthesis)
        self.agent_memory.store_dialectical_reasoning.assert_called_once_with(
            task['id'], thesis, antithesis, synthesis)
        self.assertEqual(result, self.agent_memory.
            store_dialectical_reasoning.return_value)

    def test_retrieve_dialectical_process_succeeds(self):
        """Test retrieving a dialectical process from memory.

ReqID: N/A"""
        task_id = 'task1'
        mock_item = MagicMock(spec=MemoryItem)
        mock_item.content = (
            '{"thesis": {"id": "thesis1"}, "antithesis": {"id": "antithesis1"}, "synthesis": {"id": "synthesis1"}}'
            )
        self.agent_memory.retrieve_dialectical_reasoning.return_value = (
            mock_item)
        result = self.wsde_memory.retrieve_dialectical_process(task_id)
        self.agent_memory.retrieve_dialectical_reasoning.assert_called_once_with(
            task_id)
        self.assertEqual(result['thesis']['id'], 'thesis1')
        self.assertEqual(result['antithesis']['id'], 'antithesis1')
        self.assertEqual(result['synthesis']['id'], 'synthesis1')

    def test_store_agent_solution_succeeds(self):
        """Test storing an agent solution in memory.

ReqID: N/A"""
        agent_id = 'agent1'
        task = {'id': 'task1', 'description': 'Test task'}
        solution = {'id': 'solution1', 'content': 'Test solution'}
        result = self.wsde_memory.store_agent_solution(agent_id, task, solution
            )
        self.agent_memory.store_agent_solution.assert_called_once_with(agent_id
            , task, solution)
        self.assertEqual(result, self.agent_memory.store_agent_solution.
            return_value)

    def test_retrieve_agent_solutions_succeeds(self):
        """Test retrieving agent solutions from memory.

ReqID: N/A"""
        task_id = 'task1'
        mock_items = [MagicMock(spec=MemoryItem), MagicMock(spec=MemoryItem)]
        self.agent_memory.retrieve_agent_solutions.return_value = mock_items
        results = self.wsde_memory.retrieve_agent_solutions(task_id)
        self.agent_memory.retrieve_agent_solutions.assert_called_once_with(
            task_id)
        self.assertEqual(results, mock_items)

    def test_store_team_context_succeeds(self):
        """Test storing team context in memory.

ReqID: N/A"""
        context_data = {'key': 'value', 'nested': {'data': 'nested value'}}
        self.wsde_memory.store_team_context(context_data)
        self.context_manager.add_to_context.assert_called_once()
        context_key, context_value = (self.context_manager.add_to_context.
            call_args[0])
        self.assertEqual(context_key, 'wsde_team')
        self.assertEqual(context_value, context_data)

    def test_retrieve_team_context_succeeds(self):
        """Test retrieving team context from memory.

ReqID: N/A"""
        context_data = {'key': 'value', 'nested': {'data': 'nested value'}}
        self.context_manager.get_from_context.return_value = context_data
        result = self.wsde_memory.retrieve_team_context()
        self.context_manager.get_from_context.assert_called_once_with(
            'wsde_team')
        self.assertEqual(result, context_data)

    def test_search_similar_solutions_succeeds(self):
        """Test searching for similar solutions using vector similarity.

ReqID: N/A"""
        query = 'How to implement a feature'
        mock_vectors = [MagicMock(), MagicMock()]
        self.agent_memory.search_similar_solutions.return_value = mock_vectors
        results = self.wsde_memory.search_similar_solutions(query)
        self.agent_memory.search_similar_solutions.assert_called_once_with(
            query, top_k=5)
        self.assertEqual(results, mock_vectors)

    def test_store_agent_solution_with_edrr_phase_has_expected(self):
        """Test storing an agent solution with EDRR phase tagging.

ReqID: N/A"""
        agent_id = 'agent1'
        task = {'id': 'task1', 'description': 'Test task'}
        solution = {'id': 'solution1', 'content': 'Test solution'}
        edrr_phase = 'Expand'
        mock_item = MagicMock(spec=MemoryItem)
        mock_item.metadata = {}
        self.memory_store.get_item.return_value = mock_item
        self.agent_memory.store_agent_solution.return_value = 'item123'
        result = self.wsde_memory.store_agent_solution(agent_id, task,
            solution, edrr_phase)
        self.agent_memory.store_agent_solution.assert_called_once_with(agent_id
            , task, solution)
        self.memory_store.get_item.assert_called_once_with('item123')
        self.memory_store.update_item.assert_called_once()
        self.assertEqual(mock_item.metadata.get('edrr_phase'), edrr_phase)
        self.assertEqual(result, 'item123')

    def test_retrieve_solutions_by_edrr_phase_has_expected(self):
        """Test retrieving agent solutions filtered by EDRR phase.

ReqID: N/A"""
        task_id = 'task1'
        edrr_phase = 'Expand'
        expand_item = MagicMock(spec=MemoryItem)
        expand_item.metadata = {'edrr_phase': 'Expand'}
        differentiate_item = MagicMock(spec=MemoryItem)
        differentiate_item.metadata = {'edrr_phase': 'Differentiate'}
        refine_item = MagicMock(spec=MemoryItem)
        refine_item.metadata = {'edrr_phase': 'Refine'}
        self.agent_memory.retrieve_agent_solutions.return_value = [expand_item,
            differentiate_item, refine_item]
        results = self.wsde_memory.retrieve_solutions_by_edrr_phase(task_id,
            edrr_phase)
        self.agent_memory.retrieve_agent_solutions.assert_called_once_with(
            task_id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], expand_item)

    def test_query_knowledge_graph_succeeds(self):
        """Test querying the knowledge graph.

ReqID: N/A"""
        query = 'SPARQL query'
        mock_results = [{'subject': 's1', 'predicate': 'p1', 'object': 'o1'}]
        self.memory_store.query_graph = MagicMock(return_value=mock_results)
        results = self.wsde_memory.query_knowledge_graph(query)
        self.memory_store.query_graph.assert_called_once_with(query, limit=10)
        self.assertEqual(results, mock_results)

    def test_query_knowledge_graph_not_supported_succeeds(self):
        """Test querying the knowledge graph when not supported.

ReqID: N/A"""
        query = 'SPARQL query'
        if hasattr(self.memory_store, 'query_graph'):
            delattr(self.memory_store, 'query_graph')
        with self.assertRaises(ValueError):
            self.wsde_memory.query_knowledge_graph(query)

    def test_query_related_concepts_succeeds(self):
        """Test querying for concepts related to a given concept.

ReqID: N/A"""
        concept = 'authentication'
        mock_results = [{'related_concept': 'security', 'relationship':
            'requires'}, {'related_concept': 'password', 'relationship':
            'uses'}]
        self.memory_store.query_graph = MagicMock(return_value=mock_results)
        results = self.wsde_memory.query_related_concepts(concept)
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)

    def test_query_concept_relationships_succeeds(self):
        """Test querying for relationships between concepts.

ReqID: N/A"""
        concept1 = 'authentication'
        concept2 = 'security'
        mock_results = [{'relationship': 'requires', 'direction': 'outgoing'}]
        self.memory_store.query_graph = MagicMock(return_value=mock_results)
        results = self.wsde_memory.query_concept_relationships(concept1,
            concept2)
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)

    def test_query_by_concept_type_succeeds(self):
        """Test querying for concepts of a specific type.

ReqID: N/A"""
        concept_type = 'security_concept'
        mock_results = [{'concept': 'authentication', 'properties': {
            'description': 'User verification'}}, {'concept': 'encryption',
            'properties': {'description': 'Data protection'}}]
        self.memory_store.query_graph = MagicMock(return_value=mock_results)
        results = self.wsde_memory.query_by_concept_type(concept_type)
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)

    def test_query_knowledge_for_task_succeeds(self):
        """Test querying for knowledge relevant to a specific task.

ReqID: N/A"""
        task = {'type': 'security_implementation', 'description':
            'Implement a secure authentication system', 'requirements': [
            'user authentication', 'password security']}
        mock_results = [{'concept': 'authentication', 'relevance': 0.9}, {
            'concept': 'password', 'relevance': 0.8}, {'concept':
            'encryption', 'relevance': 0.7}]
        self.memory_store.query_graph = MagicMock(return_value=mock_results)
        results = self.wsde_memory.query_knowledge_for_task(task)
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)
