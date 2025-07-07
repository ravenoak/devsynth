"""Integration tests for memory system integration with agents.

This test verifies that agents can store and retrieve information from the memory system,
and that the memory system correctly manages agent-specific memory.
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import MagicMock, patch

from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.adapters.tinydb_memory_adapter import TinyDBMemoryAdapter
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration


class TestMemoryAgentIntegration:
    """Test the integration between the memory system and agents."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def memory_adapter(self, temp_dir):
        """Create a memory adapter for testing."""
        db_path = os.path.join(temp_dir, "memory.json")
        return TinyDBMemoryAdapter(db_path=db_path)

    @pytest.fixture
    def memory_manager(self, memory_adapter):
        """Create a memory manager for testing."""
        return MemoryManager(adapters={"default": memory_adapter})

    @pytest.fixture
    def agent(self):
        """Create an agent for testing."""
        return UnifiedAgent(
            name="TestAgent",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"])
        )

    @pytest.fixture
    def agent_memory(self, memory_manager, agent):
        """Create an agent memory integration for testing."""
        return AgentMemoryIntegration(memory_manager, agent)

    def test_agent_can_store_and_retrieve_memory(self, agent_memory):
        """Test that an agent can store and retrieve memory."""
        # Store a memory item
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        
        memory_id = agent_memory.store_memory(memory_content, memory_type, metadata)
        
        # Verify that the memory item was stored
        assert memory_id is not None
        
        # Retrieve the memory item
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        
        # Verify that the retrieved item matches the stored item
        assert retrieved_item is not None
        assert retrieved_item.content == memory_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata["source"] == metadata["source"]
        assert retrieved_item.metadata["confidence"] == metadata["confidence"]
        assert retrieved_item.metadata["agent_name"] == "TestAgent"

    def test_agent_can_search_memory(self, agent_memory):
        """Test that an agent can search memory."""
        # Store multiple memory items
        for i in range(5):
            memory_content = {"key": f"value{i}", "number": i}
            memory_type = MemoryType.KNOWLEDGE
            metadata = {"source": "test", "confidence": 0.9 - i * 0.1}
            
            agent_memory.store_memory(memory_content, memory_type, metadata)
        
        # Search for memory items with a specific key
        search_results = agent_memory.search_memory({"key": "value2"})
        
        # Verify that the search returned the expected results
        assert len(search_results) == 1
        assert search_results[0].content["key"] == "value2"
        assert search_results[0].content["number"] == 2
        
        # Search for memory items with a specific metadata value
        search_results = agent_memory.search_memory({"confidence": 0.9})
        
        # Verify that the search returned the expected results
        assert len(search_results) == 1
        assert search_results[0].content["key"] == "value0"
        assert search_results[0].content["number"] == 0
        
        # Search for memory items with a specific agent name
        search_results = agent_memory.search_memory({"agent_name": "TestAgent"})
        
        # Verify that the search returned the expected results
        assert len(search_results) == 5

    def test_agent_can_update_memory(self, agent_memory):
        """Test that an agent can update memory."""
        # Store a memory item
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        
        memory_id = agent_memory.store_memory(memory_content, memory_type, metadata)
        
        # Update the memory item
        updated_content = {"key": "updated_value", "number": 43}
        updated_metadata = {"source": "test", "confidence": 0.95}
        
        agent_memory.update_memory(memory_id, updated_content, updated_metadata)
        
        # Retrieve the updated memory item
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        
        # Verify that the retrieved item has been updated
        assert retrieved_item is not None
        assert retrieved_item.content == updated_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata["source"] == updated_metadata["source"]
        assert retrieved_item.metadata["confidence"] == updated_metadata["confidence"]
        assert retrieved_item.metadata["agent_name"] == "TestAgent"

    def test_agent_can_delete_memory(self, agent_memory):
        """Test that an agent can delete memory."""
        # Store a memory item
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        
        memory_id = agent_memory.store_memory(memory_content, memory_type, metadata)
        
        # Verify that the memory item was stored
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        
        # Delete the memory item
        agent_memory.delete_memory(memory_id)
        
        # Verify that the memory item was deleted
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is None

    def test_multiple_agents_can_share_memory(self, memory_manager):
        """Test that multiple agents can share memory."""
        # Create two agents
        agent1 = UnifiedAgent(
            name="Agent1",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"])
        )
        agent2 = UnifiedAgent(
            name="Agent2",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"])
        )
        
        # Create agent memory integrations for both agents
        agent1_memory = AgentMemoryIntegration(memory_manager, agent1)
        agent2_memory = AgentMemoryIntegration(memory_manager, agent2)
        
        # Agent1 stores a memory item
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9, "shared": True}
        
        memory_id = agent1_memory.store_memory(memory_content, memory_type, metadata)
        
        # Agent2 retrieves the memory item
        retrieved_item = agent2_memory.retrieve_memory(memory_id)
        
        # Verify that Agent2 can retrieve the memory item stored by Agent1
        assert retrieved_item is not None
        assert retrieved_item.content == memory_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata["source"] == metadata["source"]
        assert retrieved_item.metadata["confidence"] == metadata["confidence"]
        assert retrieved_item.metadata["agent_name"] == "Agent1"
        assert retrieved_item.metadata["shared"] == True

    def test_agent_memory_isolation(self, memory_manager):
        """Test that agent memory can be isolated."""
        # Create two agents
        agent1 = UnifiedAgent(
            name="Agent1",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"])
        )
        agent2 = UnifiedAgent(
            name="Agent2",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"])
        )
        
        # Create agent memory integrations for both agents
        agent1_memory = AgentMemoryIntegration(memory_manager, agent1)
        agent2_memory = AgentMemoryIntegration(memory_manager, agent2)
        
        # Agent1 stores a private memory item
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9, "private": True}
        
        memory_id = agent1_memory.store_memory(memory_content, memory_type, metadata)
        
        # Agent1 can retrieve the memory item
        retrieved_item = agent1_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        
        # Agent2 cannot retrieve the private memory item stored by Agent1
        # This assumes that the AgentMemoryIntegration respects the "private" flag
        # If it doesn't, this test will fail
        retrieved_item = agent2_memory.retrieve_memory(memory_id)
        assert retrieved_item is None or retrieved_item.metadata.get("private") != True

    def test_agent_memory_with_context(self, agent_memory):
        """Test that an agent can store and retrieve memory with context."""
        # Store a memory item with context
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        context = {"task_id": "task123", "phase": "testing"}
        
        memory_id = agent_memory.store_memory_with_context(memory_content, memory_type, metadata, context)
        
        # Verify that the memory item was stored
        assert memory_id is not None
        
        # Retrieve the memory item with context
        retrieved_items = agent_memory.retrieve_memory_with_context(context)
        
        # Verify that the retrieved item matches the stored item
        assert len(retrieved_items) == 1
        assert retrieved_items[0].content == memory_content
        assert retrieved_items[0].memory_type == memory_type
        assert retrieved_items[0].metadata["source"] == metadata["source"]
        assert retrieved_items[0].metadata["confidence"] == metadata["confidence"]
        assert retrieved_items[0].metadata["agent_name"] == "TestAgent"
        assert retrieved_items[0].metadata["context"]["task_id"] == context["task_id"]
        assert retrieved_items[0].metadata["context"]["phase"] == context["phase"]