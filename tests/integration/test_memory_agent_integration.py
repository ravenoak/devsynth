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
    """Test the integration between the memory system and agents.

ReqID: N/A"""

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
        db_path = os.path.join(temp_dir, 'memory.json')
        return TinyDBMemoryAdapter(db_path=db_path)

    @pytest.fixture
    def memory_manager(self, memory_adapter):
        """Create a memory manager for testing."""
        return MemoryManager(adapters={'default': memory_adapter})

    @pytest.fixture
    def agent(self):
        """Create an agent for testing."""
        return UnifiedAgent(name='TestAgent', agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=['testing', 'memory']))

    @pytest.fixture
    def agent_memory(self, memory_manager, agent):
        """Create an agent memory integration for testing."""
        return AgentMemoryIntegration(memory_manager, agent)

    def test_agent_can_store_and_retrieve_memory_succeeds(self, agent_memory):
        """Test that an agent can store and retrieve memory.

ReqID: N/A"""
        memory_content = {'key': 'value', 'number': 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {'source': 'test', 'confidence': 0.9}
        memory_id = agent_memory.store_memory(memory_content, memory_type,
            metadata)
        assert memory_id is not None
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        assert retrieved_item.content == memory_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata['source'] == metadata['source']
        assert retrieved_item.metadata['confidence'] == metadata['confidence']
        assert retrieved_item.metadata['agent_name'] == 'TestAgent'

    def test_agent_can_search_memory_succeeds(self, agent_memory):
        """Test that an agent can search memory.

ReqID: N/A"""
        for i in range(5):
            memory_content = {'key': f'value{i}', 'number': i}
            memory_type = MemoryType.KNOWLEDGE
            metadata = {'source': 'test', 'confidence': 0.9 - i * 0.1}
            agent_memory.store_memory(memory_content, memory_type, metadata)
        search_results = agent_memory.search_memory({'key': 'value2'})
        assert len(search_results) == 1
        assert search_results[0].content['key'] == 'value2'
        assert search_results[0].content['number'] == 2
        search_results = agent_memory.search_memory({'confidence': 0.9})
        assert len(search_results) == 1
        assert search_results[0].content['key'] == 'value0'
        assert search_results[0].content['number'] == 0
        search_results = agent_memory.search_memory({'agent_name': 'TestAgent'}
            )
        assert len(search_results) == 5

    def test_agent_can_update_memory_succeeds(self, agent_memory):
        """Test that an agent can update memory.

ReqID: N/A"""
        memory_content = {'key': 'value', 'number': 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {'source': 'test', 'confidence': 0.9}
        memory_id = agent_memory.store_memory(memory_content, memory_type,
            metadata)
        updated_content = {'key': 'updated_value', 'number': 43}
        updated_metadata = {'source': 'test', 'confidence': 0.95}
        agent_memory.update_memory(memory_id, updated_content, updated_metadata
            )
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        assert retrieved_item.content == updated_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata['source'] == updated_metadata['source']
        assert retrieved_item.metadata['confidence'] == updated_metadata[
            'confidence']
        assert retrieved_item.metadata['agent_name'] == 'TestAgent'

    def test_agent_can_delete_memory_succeeds(self, agent_memory):
        """Test that an agent can delete memory.

ReqID: N/A"""
        memory_content = {'key': 'value', 'number': 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {'source': 'test', 'confidence': 0.9}
        memory_id = agent_memory.store_memory(memory_content, memory_type,
            metadata)
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        agent_memory.delete_memory(memory_id)
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is None

    def test_multiple_agents_can_share_memory_succeeds(self, memory_manager):
        """Test that multiple agents can share memory.

ReqID: N/A"""
        agent1 = UnifiedAgent(name='Agent1', agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=['testing', 'memory']))
        agent2 = UnifiedAgent(name='Agent2', agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=['testing', 'memory']))
        agent1_memory = AgentMemoryIntegration(memory_manager, agent1)
        agent2_memory = AgentMemoryIntegration(memory_manager, agent2)
        memory_content = {'key': 'value', 'number': 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {'source': 'test', 'confidence': 0.9, 'shared': True}
        memory_id = agent1_memory.store_memory(memory_content, memory_type,
            metadata)
        retrieved_item = agent2_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        assert retrieved_item.content == memory_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata['source'] == metadata['source']
        assert retrieved_item.metadata['confidence'] == metadata['confidence']
        assert retrieved_item.metadata['agent_name'] == 'Agent1'
        assert retrieved_item.metadata['shared'] == True

    def test_agent_memory_isolation_succeeds(self, memory_manager):
        """Test that agent memory can be isolated.

ReqID: N/A"""
        agent1 = UnifiedAgent(name='Agent1', agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=['testing', 'memory']))
        agent2 = UnifiedAgent(name='Agent2', agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=['testing', 'memory']))
        agent1_memory = AgentMemoryIntegration(memory_manager, agent1)
        agent2_memory = AgentMemoryIntegration(memory_manager, agent2)
        memory_content = {'key': 'value', 'number': 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {'source': 'test', 'confidence': 0.9, 'private': True}
        memory_id = agent1_memory.store_memory(memory_content, memory_type,
            metadata)
        retrieved_item = agent1_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        retrieved_item = agent2_memory.retrieve_memory(memory_id)
        assert retrieved_item is None or retrieved_item.metadata.get('private'
            ) != True

    def test_agent_memory_with_context_succeeds(self, agent_memory):
        """Test that an agent can store and retrieve memory with context.

ReqID: N/A"""
        memory_content = {'key': 'value', 'number': 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {'source': 'test', 'confidence': 0.9}
        context = {'task_id': 'task123', 'phase': 'testing'}
        memory_id = agent_memory.store_memory_with_context(memory_content,
            memory_type, metadata, context)
        assert memory_id is not None
        retrieved_items = agent_memory.retrieve_memory_with_context(context)
        assert len(retrieved_items) == 1
        assert retrieved_items[0].content == memory_content
        assert retrieved_items[0].memory_type == memory_type
        assert retrieved_items[0].metadata['source'] == metadata['source']
        assert retrieved_items[0].metadata['confidence'] == metadata[
            'confidence']
        assert retrieved_items[0].metadata['agent_name'] == 'TestAgent'
        assert retrieved_items[0].metadata['context']['task_id'] == context[
            'task_id']
        assert retrieved_items[0].metadata['context']['phase'] == context[
            'phase']
