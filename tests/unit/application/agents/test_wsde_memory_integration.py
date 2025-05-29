import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.wsde import WSDETeam
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration
from devsynth.application.agents.wsde_memory_integration import WSDEMemoryIntegration


class TestWSDEMemoryIntegration(unittest.TestCase):
    """Test the integration between WSDE and the memory system."""

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

        # Create a mock agent memory integration
        self.agent_memory = MagicMock(spec=AgentMemoryIntegration)

        # Create the WSDE memory integration
        self.wsde_memory = WSDEMemoryIntegration(
            memory_adapter=self.memory_adapter,
            wsde_team=self.wsde_team,
            agent_memory=self.agent_memory
        )

    def test_store_dialectical_process(self):
        """Test storing a dialectical process in memory."""
        # Arrange
        task = {"id": "task1", "description": "Test task"}
        thesis = {"id": "thesis1", "content": "Thesis content"}
        antithesis = {"id": "antithesis1", "content": "Antithesis content"}
        synthesis = {"id": "synthesis1", "content": "Synthesis content"}

        # Act
        result = self.wsde_memory.store_dialectical_process(task, thesis, antithesis, synthesis)

        # Assert
        self.agent_memory.store_dialectical_reasoning.assert_called_once_with(
            task["id"], thesis, antithesis, synthesis
        )
        self.assertEqual(result, self.agent_memory.store_dialectical_reasoning.return_value)

    def test_retrieve_dialectical_process(self):
        """Test retrieving a dialectical process from memory."""
        # Arrange
        task_id = "task1"
        mock_item = MagicMock(spec=MemoryItem)
        mock_item.content = '{"thesis": {"id": "thesis1"}, "antithesis": {"id": "antithesis1"}, "synthesis": {"id": "synthesis1"}}'
        self.agent_memory.retrieve_dialectical_reasoning.return_value = mock_item

        # Act
        result = self.wsde_memory.retrieve_dialectical_process(task_id)

        # Assert
        self.agent_memory.retrieve_dialectical_reasoning.assert_called_once_with(task_id)
        self.assertEqual(result["thesis"]["id"], "thesis1")
        self.assertEqual(result["antithesis"]["id"], "antithesis1")
        self.assertEqual(result["synthesis"]["id"], "synthesis1")

    def test_store_agent_solution(self):
        """Test storing an agent solution in memory."""
        # Arrange
        agent_id = "agent1"
        task = {"id": "task1", "description": "Test task"}
        solution = {"id": "solution1", "content": "Test solution"}

        # Act
        result = self.wsde_memory.store_agent_solution(agent_id, task, solution)

        # Assert
        self.agent_memory.store_agent_solution.assert_called_once_with(agent_id, task, solution)
        self.assertEqual(result, self.agent_memory.store_agent_solution.return_value)

    def test_retrieve_agent_solutions(self):
        """Test retrieving agent solutions from memory."""
        # Arrange
        task_id = "task1"
        mock_items = [MagicMock(spec=MemoryItem), MagicMock(spec=MemoryItem)]
        self.agent_memory.retrieve_agent_solutions.return_value = mock_items

        # Act
        results = self.wsde_memory.retrieve_agent_solutions(task_id)

        # Assert
        self.agent_memory.retrieve_agent_solutions.assert_called_once_with(task_id)
        self.assertEqual(results, mock_items)

    def test_store_team_context(self):
        """Test storing team context in memory."""
        # Arrange
        context_data = {"key": "value", "nested": {"data": "nested value"}}

        # Act
        self.wsde_memory.store_team_context(context_data)

        # Assert
        self.context_manager.add_to_context.assert_called_once()
        context_key, context_value = self.context_manager.add_to_context.call_args[0]
        self.assertEqual(context_key, "wsde_team")
        self.assertEqual(context_value, context_data)

    def test_retrieve_team_context(self):
        """Test retrieving team context from memory."""
        # Arrange
        context_data = {"key": "value", "nested": {"data": "nested value"}}
        self.context_manager.get_from_context.return_value = context_data

        # Act
        result = self.wsde_memory.retrieve_team_context()

        # Assert
        self.context_manager.get_from_context.assert_called_once_with("wsde_team")
        self.assertEqual(result, context_data)

    def test_search_similar_solutions(self):
        """Test searching for similar solutions using vector similarity."""
        # Arrange
        query = "How to implement a feature"
        mock_vectors = [MagicMock(), MagicMock()]
        self.agent_memory.search_similar_solutions.return_value = mock_vectors

        # Act
        results = self.wsde_memory.search_similar_solutions(query)

        # Assert
        self.agent_memory.search_similar_solutions.assert_called_once_with(query, top_k=5)
        self.assertEqual(results, mock_vectors)

    def test_store_agent_solution_with_edrr_phase(self):
        """Test storing an agent solution with EDRR phase tagging."""
        # Arrange
        agent_id = "agent1"
        task = {"id": "task1", "description": "Test task"}
        solution = {"id": "solution1", "content": "Test solution"}
        edrr_phase = "Expand"

        # Mock the memory item
        mock_item = MagicMock(spec=MemoryItem)
        mock_item.metadata = {}
        self.memory_store.get_item.return_value = mock_item

        # Mock the store_agent_solution method
        self.agent_memory.store_agent_solution.return_value = "item123"

        # Act
        result = self.wsde_memory.store_agent_solution(agent_id, task, solution, edrr_phase)

        # Assert
        self.agent_memory.store_agent_solution.assert_called_once_with(agent_id, task, solution)
        self.memory_store.get_item.assert_called_once_with("item123")
        self.memory_store.update_item.assert_called_once()
        self.assertEqual(mock_item.metadata.get("edrr_phase"), edrr_phase)
        self.assertEqual(result, "item123")

    def test_retrieve_solutions_by_edrr_phase(self):
        """Test retrieving agent solutions filtered by EDRR phase."""
        # Arrange
        task_id = "task1"
        edrr_phase = "Expand"

        # Create mock memory items with different EDRR phases
        expand_item = MagicMock(spec=MemoryItem)
        expand_item.metadata = {"edrr_phase": "Expand"}

        differentiate_item = MagicMock(spec=MemoryItem)
        differentiate_item.metadata = {"edrr_phase": "Differentiate"}

        refine_item = MagicMock(spec=MemoryItem)
        refine_item.metadata = {"edrr_phase": "Refine"}

        # Mock the retrieve_agent_solutions method to return all items
        self.agent_memory.retrieve_agent_solutions.return_value = [
            expand_item, differentiate_item, refine_item
        ]

        # Act
        results = self.wsde_memory.retrieve_solutions_by_edrr_phase(task_id, edrr_phase)

        # Assert
        self.agent_memory.retrieve_agent_solutions.assert_called_once_with(task_id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], expand_item)

    def test_query_knowledge_graph(self):
        """Test querying the knowledge graph."""
        # Arrange
        query = "SPARQL query"
        mock_results = [{"subject": "s1", "predicate": "p1", "object": "o1"}]

        # Mock the query_graph method
        self.memory_store.query_graph = MagicMock(return_value=mock_results)

        # Act
        results = self.wsde_memory.query_knowledge_graph(query)

        # Assert
        self.memory_store.query_graph.assert_called_once_with(query, limit=10)
        self.assertEqual(results, mock_results)

    def test_query_knowledge_graph_not_supported(self):
        """Test querying the knowledge graph when not supported."""
        # Arrange
        query = "SPARQL query"

        # Remove the query_graph method from the mock
        if hasattr(self.memory_store, "query_graph"):
            delattr(self.memory_store, "query_graph")

        # Act and Assert
        with self.assertRaises(ValueError):
            self.wsde_memory.query_knowledge_graph(query)

    def test_query_related_concepts(self):
        """Test querying for concepts related to a given concept."""
        # Arrange
        concept = "authentication"
        mock_results = [
            {"related_concept": "security", "relationship": "requires"},
            {"related_concept": "password", "relationship": "uses"}
        ]

        # Mock the query_graph method
        self.memory_store.query_graph = MagicMock(return_value=mock_results)

        # Act
        results = self.wsde_memory.query_related_concepts(concept)

        # Assert
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)

    def test_query_concept_relationships(self):
        """Test querying for relationships between concepts."""
        # Arrange
        concept1 = "authentication"
        concept2 = "security"
        mock_results = [
            {"relationship": "requires", "direction": "outgoing"}
        ]

        # Mock the query_graph method
        self.memory_store.query_graph = MagicMock(return_value=mock_results)

        # Act
        results = self.wsde_memory.query_concept_relationships(concept1, concept2)

        # Assert
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)

    def test_query_by_concept_type(self):
        """Test querying for concepts of a specific type."""
        # Arrange
        concept_type = "security_concept"
        mock_results = [
            {"concept": "authentication", "properties": {"description": "User verification"}},
            {"concept": "encryption", "properties": {"description": "Data protection"}}
        ]

        # Mock the query_graph method
        self.memory_store.query_graph = MagicMock(return_value=mock_results)

        # Act
        results = self.wsde_memory.query_by_concept_type(concept_type)

        # Assert
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)

    def test_query_knowledge_for_task(self):
        """Test querying for knowledge relevant to a specific task."""
        # Arrange
        task = {
            "type": "security_implementation",
            "description": "Implement a secure authentication system",
            "requirements": ["user authentication", "password security"]
        }
        mock_results = [
            {"concept": "authentication", "relevance": 0.9},
            {"concept": "password", "relevance": 0.8},
            {"concept": "encryption", "relevance": 0.7}
        ]

        # Mock the query_graph method
        self.memory_store.query_graph = MagicMock(return_value=mock_results)

        # Act
        results = self.wsde_memory.query_knowledge_for_task(task)

        # Assert
        self.memory_store.query_graph.assert_called_once()
        self.assertEqual(results, mock_results)
