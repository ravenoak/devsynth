import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration


class TestAgentMemoryIntegration(unittest.TestCase):
    """Test the integration between agents and the memory system."""

    def setUp(self):
        """Set up the test environment."""
        # Create a mock memory system adapter
        self.memory_adapter = MagicMock(spec=MemorySystemAdapter)
        self.memory_store = MagicMock()
        self.context_manager = MagicMock()
        self.vector_store = MagicMock()

        # Configure the mock memory adapter
        self.memory_adapter.get_memory_store.return_value = self.memory_store
        self.memory_adapter.get_context_manager.return_value = self.context_manager
        self.memory_adapter.get_vector_store.return_value = self.vector_store
        self.memory_adapter.has_vector_store.return_value = True

        # Create a mock WSDE team
        self.wsde_team = MagicMock(spec=WSDETeam)

        # Create the agent memory integration
        self.agent_memory = AgentMemoryIntegration(
            memory_adapter=self.memory_adapter,
            wsde_team=self.wsde_team
        )

    def test_store_agent_solution(self):
        """Test storing an agent solution in memory."""
        # Arrange
        agent_id = "agent1"
        task = {"id": "task1", "description": "Test task"}
        solution = {"id": "solution1", "content": "Test solution"}

        # Act
        result = self.agent_memory.store_agent_solution(agent_id, task, solution)

        # Assert
        self.memory_store.store.assert_called_once()
        stored_item = self.memory_store.store.call_args[0][0]
        self.assertEqual(stored_item.memory_type, MemoryType.SOLUTION)
        self.assertEqual(stored_item.metadata.get("agent_id"), agent_id)
        self.assertEqual(stored_item.metadata.get("task_id"), task["id"])
        self.assertEqual(stored_item.metadata.get("solution_id"), solution["id"])
        self.assertEqual(result, self.memory_store.store.return_value)

    def test_retrieve_agent_solutions(self):
        """Test retrieving agent solutions from memory."""
        # Arrange
        task_id = "task1"
        mock_items = [
            MemoryItem(
                id="item1",
                content="Solution 1",
                memory_type=MemoryType.SOLUTION,
                metadata={"task_id": task_id, "agent_id": "agent1"}
            ),
            MemoryItem(
                id="item2",
                content="Solution 2",
                memory_type=MemoryType.SOLUTION,
                metadata={"task_id": task_id, "agent_id": "agent2"}
            )
        ]
        self.memory_store.search.return_value = mock_items

        # Act
        results = self.agent_memory.retrieve_agent_solutions(task_id)

        # Assert
        self.memory_store.search.assert_called_once()
        search_query = self.memory_store.search.call_args[0][0]
        self.assertEqual(search_query["memory_type"], MemoryType.SOLUTION)
        self.assertEqual(search_query["metadata.task_id"], task_id)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].content, "Solution 1")
        self.assertEqual(results[1].content, "Solution 2")

    def test_store_dialectical_reasoning(self):
        """Test storing dialectical reasoning in memory."""
        # Arrange
        task_id = "task1"
        thesis = {"id": "thesis1", "content": "Thesis content"}
        antithesis = {"id": "antithesis1", "content": "Antithesis content"}
        synthesis = {"id": "synthesis1", "content": "Synthesis content"}

        # Act
        result = self.agent_memory.store_dialectical_reasoning(task_id, thesis, antithesis, synthesis)

        # Assert
        self.memory_store.store.assert_called_once()
        stored_item = self.memory_store.store.call_args[0][0]
        self.assertEqual(stored_item.memory_type, MemoryType.DIALECTICAL_REASONING)
        self.assertEqual(stored_item.metadata.get("task_id"), task_id)
        self.assertEqual(stored_item.metadata.get("thesis_id"), thesis["id"])
        self.assertEqual(stored_item.metadata.get("antithesis_id"), antithesis["id"])
        self.assertEqual(stored_item.metadata.get("synthesis_id"), synthesis["id"])
        self.assertEqual(result, self.memory_store.store.return_value)

    def test_retrieve_dialectical_reasoning(self):
        """Test retrieving dialectical reasoning from memory."""
        # Arrange
        task_id = "task1"
        mock_item = MemoryItem(
            id="item1",
            content="Dialectical reasoning content",
            memory_type=MemoryType.DIALECTICAL_REASONING,
            metadata={
                "task_id": task_id,
                "thesis_id": "thesis1",
                "antithesis_id": "antithesis1",
                "synthesis_id": "synthesis1"
            }
        )
        self.memory_store.search.return_value = [mock_item]

        # Act
        result = self.agent_memory.retrieve_dialectical_reasoning(task_id)

        # Assert
        self.memory_store.search.assert_called_once()
        search_query = self.memory_store.search.call_args[0][0]
        self.assertEqual(search_query["memory_type"], MemoryType.DIALECTICAL_REASONING)
        self.assertEqual(search_query["metadata.task_id"], task_id)
        self.assertEqual(result, mock_item)

    def test_store_agent_context(self):
        """Test storing agent context in memory."""
        # Arrange
        agent_id = "agent1"
        context_data = {"key": "value", "nested": {"data": "nested value"}}

        # Act
        self.agent_memory.store_agent_context(agent_id, context_data)

        # Assert
        self.context_manager.add_to_context.assert_called_once()
        context_key, context_value = self.context_manager.add_to_context.call_args[0]
        self.assertEqual(context_key, f"agent:{agent_id}")
        self.assertEqual(context_value, context_data)

    def test_retrieve_agent_context(self):
        """Test retrieving agent context from memory."""
        # Arrange
        agent_id = "agent1"
        context_data = {"key": "value", "nested": {"data": "nested value"}}
        self.context_manager.get_from_context.return_value = context_data

        # Act
        result = self.agent_memory.retrieve_agent_context(agent_id)

        # Assert
        self.context_manager.get_from_context.assert_called_once_with(f"agent:{agent_id}")
        self.assertEqual(result, context_data)

    def test_search_similar_solutions(self):
        """Test searching for similar solutions using vector similarity."""
        # Arrange
        query = "How to implement a feature"
        mock_vectors = [MagicMock(), MagicMock()]
        self.vector_store.similarity_search.return_value = mock_vectors

        # Act
        results = self.agent_memory.search_similar_solutions(query)

        # Assert
        self.vector_store.similarity_search.assert_called_once()
        self.assertEqual(results, mock_vectors)

    def test_search_similar_solutions_no_vector_store(self):
        """Test searching for similar solutions when no vector store is available."""
        # Arrange
        query = "How to implement a feature"
        self.memory_adapter.has_vector_store.return_value = False
        self.agent_memory.vector_store = None

        # Act
        results = self.agent_memory.search_similar_solutions(query)

        # Assert
        self.vector_store.similarity_search.assert_not_called()
        self.assertEqual(results, [])
