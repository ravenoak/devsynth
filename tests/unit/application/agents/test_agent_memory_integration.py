import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration


class TestAgentMemoryIntegration(unittest.TestCase):
    """Test the integration between agents and the memory system.

ReqID: N/A"""

    def setUp(self):
        """Set up the test environment."""
        self.memory_adapter = MagicMock(spec=MemorySystemAdapter)
        self.memory_store = MagicMock()
        self.context_manager = MagicMock()
        self.vector_store = MagicMock()
        self.memory_adapter.get_memory_store.return_value = self.memory_store
        self.memory_adapter.get_context_manager.return_value = (self.
            context_manager)
        self.memory_adapter.get_vector_store.return_value = self.vector_store
        self.memory_adapter.has_vector_store.return_value = True
        self.wsde_team = MagicMock(spec=WSDETeam)
        self.wsde_team.name = "TestAgent"
        self.agent_memory = AgentMemoryIntegration(memory_adapter=self.
            memory_adapter, wsde_team=self.wsde_team)

    def test_store_agent_solution_succeeds(self):
        """Test storing an agent solution in memory.

ReqID: N/A"""
        agent_id = 'agent1'
        task = {'id': 'task1', 'description': 'Test task'}
        solution = {'id': 'solution1', 'content': 'Test solution'}
        result = self.agent_memory.store_agent_solution(agent_id, task,
            solution)
        self.memory_store.store.assert_called_once()
        stored_item = self.memory_store.store.call_args[0][0]
        self.assertEqual(stored_item.memory_type, MemoryType.SOLUTION)
        self.assertEqual(stored_item.metadata.get('agent_id'), agent_id)
        self.assertEqual(stored_item.metadata.get('task_id'), task['id'])
        self.assertEqual(stored_item.metadata.get('solution_id'), solution[
            'id'])
        self.assertEqual(result, self.memory_store.store.return_value)

    def test_retrieve_agent_solutions_succeeds(self):
        """Test retrieving agent solutions from memory.

ReqID: N/A"""
        task_id = 'task1'
        mock_items = [MemoryItem(id='item1', content='Solution 1',
            memory_type=MemoryType.SOLUTION, metadata={'task_id': task_id,
            'agent_id': 'agent1'}), MemoryItem(id='item2', content=
            'Solution 2', memory_type=MemoryType.SOLUTION, metadata={
            'task_id': task_id, 'agent_id': 'agent2'})]

        # Remove the 'items' attribute from memory_store
        # so the method will use search
        if hasattr(type(self.memory_store), 'items'):
            delattr(type(self.memory_store), 'items')

        # Mock the search method to return our mock items
        self.memory_store.search.return_value = mock_items

        # Call the method
        results = self.agent_memory.retrieve_agent_solutions(task_id)

        # Verify that search was called with the correct memory_type
        self.memory_store.search.assert_called_once()
        search_query = self.memory_store.search.call_args[0][0]
        self.assertEqual(search_query['memory_type'], MemoryType.SOLUTION)

        # Verify the results
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].content, 'Solution 1')
        self.assertEqual(results[1].content, 'Solution 2')

    def test_store_dialectical_reasoning_succeeds(self):
        """Test storing dialectical reasoning in memory.

ReqID: N/A"""
        task_id = 'task1'
        thesis = {'id': 'thesis1', 'content': 'Thesis content'}
        antithesis = {'id': 'antithesis1', 'content': 'Antithesis content'}
        synthesis = {'id': 'synthesis1', 'content': 'Synthesis content'}
        result = self.agent_memory.store_dialectical_reasoning(task_id,
            thesis, antithesis, synthesis)
        self.memory_store.store.assert_called_once()
        stored_item = self.memory_store.store.call_args[0][0]
        self.assertEqual(stored_item.memory_type, MemoryType.
            DIALECTICAL_REASONING)
        self.assertEqual(stored_item.metadata.get('task_id'), task_id)
        self.assertEqual(stored_item.metadata.get('thesis_id'), thesis['id'])
        self.assertEqual(stored_item.metadata.get('antithesis_id'),
            antithesis['id'])
        self.assertEqual(stored_item.metadata.get('synthesis_id'),
            synthesis['id'])
        self.assertEqual(result, self.memory_store.store.return_value)

    def test_retrieve_dialectical_reasoning_succeeds(self):
        """Test retrieving dialectical reasoning from memory.

ReqID: N/A"""
        task_id = 'task1'
        mock_item = MemoryItem(id='item1', content=
            'Dialectical reasoning content', memory_type=MemoryType.
            DIALECTICAL_REASONING, metadata={'task_id': task_id,
            'thesis_id': 'thesis1', 'antithesis_id': 'antithesis1',
            'synthesis_id': 'synthesis1'})
        self.memory_store.search.return_value = [mock_item]
        result = self.agent_memory.retrieve_dialectical_reasoning(task_id)
        self.memory_store.search.assert_called_once()
        search_query = self.memory_store.search.call_args[0][0]
        self.assertEqual(search_query['memory_type'], MemoryType.
            DIALECTICAL_REASONING)
        self.assertEqual(search_query['metadata.task_id'], task_id)
        self.assertEqual(result, mock_item)

    def test_store_agent_context_succeeds(self):
        """Test storing agent context in memory.

ReqID: N/A"""
        agent_id = 'agent1'
        context_data = {'key': 'value', 'nested': {'data': 'nested value'}}
        self.agent_memory.store_agent_context(agent_id, context_data)
        self.context_manager.add_to_context.assert_called_once()
        context_key, context_value = (self.context_manager.add_to_context.
            call_args[0])
        self.assertEqual(context_key, f'agent:{agent_id}')
        self.assertEqual(context_value, context_data)

    def test_retrieve_agent_context_succeeds(self):
        """Test retrieving agent context from memory.

ReqID: N/A"""
        agent_id = 'agent1'
        context_data = {'key': 'value', 'nested': {'data': 'nested value'}}
        self.context_manager.get_from_context.return_value = context_data
        result = self.agent_memory.retrieve_agent_context(agent_id)
        self.context_manager.get_from_context.assert_called_once_with(
            f'agent:{agent_id}')
        self.assertEqual(result, context_data)

    def test_search_similar_solutions_succeeds(self):
        """Test searching for similar solutions using vector similarity.

ReqID: N/A"""
        query = 'How to implement a feature'
        mock_vectors = [MagicMock(), MagicMock()]
        self.vector_store.similarity_search.return_value = mock_vectors
        results = self.agent_memory.search_similar_solutions(query)
        self.vector_store.similarity_search.assert_called_once()
        self.assertEqual(results, mock_vectors)

    def test_search_similar_solutions_no_vector_store_succeeds(self):
        """Test searching for similar solutions when no vector store is available.

ReqID: N/A"""
        query = 'How to implement a feature'
        self.memory_adapter.has_vector_store.return_value = False
        self.agent_memory.vector_store = None
        results = self.agent_memory.search_similar_solutions(query)
        self.vector_store.similarity_search.assert_not_called()
        self.assertEqual(results, [])

    def test_store_memory_succeeds(self):
        """Test storing generic memory."""

        content = {"a": 1}
        metadata = {"extra": True}
        memory_type = MemoryType.KNOWLEDGE

        self.agent_memory.store_memory(content, memory_type, metadata)
        self.memory_store.store.assert_called_once()
        stored_item = self.memory_store.store.call_args[0][0]
        self.assertEqual(stored_item.content, content)
        self.assertEqual(stored_item.memory_type, memory_type)
        self.assertEqual(stored_item.metadata["extra"], True)
        self.assertEqual(stored_item.metadata["agent_name"], "TestAgent")

    def test_retrieve_memory_succeeds(self):
        """Test retrieving a memory item."""

        item = MemoryItem(
            id="item1",
            content="data",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"agent_name": "TestAgent"},
        )
        self.memory_store.retrieve.return_value = item

        result = self.agent_memory.retrieve_memory("item1")
        self.memory_store.retrieve.assert_called_once_with("item1")
        self.assertEqual(result, item)

    def test_search_memory_succeeds(self):
        """Test searching memory."""

        query = {"field": "value"}
        items = [
            MemoryItem(id="1", content={"field": "value"}, memory_type=MemoryType.KNOWLEDGE)
        ]
        self.memory_store.search.return_value = items

        result = self.agent_memory.search_memory(query)
        self.memory_store.search.assert_called_once_with({})
        self.assertEqual(result, items)

    def test_update_memory_succeeds(self):
        """Test updating a memory item."""

        existing = MemoryItem(
            id="1",
            content="old",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"agent_name": "TestAgent"},
        )
        self.memory_store.retrieve.return_value = existing

        self.agent_memory.update_memory("1", "new", {"extra": 2})
        self.memory_store.retrieve.assert_called_once_with("1")
        self.memory_store.store.assert_called_once()
        updated_item = self.memory_store.store.call_args[0][0]
        self.assertEqual(updated_item.content, "new")
        self.assertEqual(updated_item.metadata["extra"], 2)
        self.assertEqual(updated_item.metadata["agent_name"], "TestAgent")

    def test_delete_memory_succeeds(self):
        """Test deleting memory."""

        self.memory_store.delete.return_value = True
        result = self.agent_memory.delete_memory("1")
        self.memory_store.delete.assert_called_once_with("1")
        self.assertTrue(result)

    def test_store_memory_with_context_succeeds(self):
        """Test storing memory with context."""

        context = {"task": "t"}
        self.agent_memory.store_memory_with_context("c", MemoryType.KNOWLEDGE, {}, context)
        self.memory_store.store.assert_called_once()
        item = self.memory_store.store.call_args[0][0]
        self.assertEqual(item.metadata["context"], context)
        self.assertEqual(item.metadata["agent_name"], "TestAgent")

    def test_retrieve_memory_with_context_succeeds(self):
        """Test retrieving memory by context."""

        context = {"task": "t"}
        items = [MemoryItem(id="1", content="c", memory_type=MemoryType.KNOWLEDGE)]
        self.memory_store.search.return_value = items
        result = self.agent_memory.retrieve_memory_with_context(context)
        self.memory_store.search.assert_called_once_with({"metadata.context": context})
        self.assertEqual(result, items)
