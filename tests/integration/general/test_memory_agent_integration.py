"""Integration tests for memory system integration with agents.

This test verifies that agents can store and retrieve information from the memory system,
and that the memory system correctly manages agent-specific memory.
"""

import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.agents.agent_memory_integration import AgentMemoryIntegration
from devsynth.application.agents.unified_agent import UnifiedAgent
from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.agent import AgentConfig, AgentType
from devsynth.domain.models.memory import MemoryItem, MemoryType


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
            config=AgentConfig(expertise=["testing", "memory"]),
        )

    @pytest.fixture
    def agent_memory(self, memory_manager, agent):
        """Create an agent memory integration for testing."""
        return AgentMemoryIntegration(memory_manager, agent)

    @pytest.mark.medium
    def test_agent_can_store_and_retrieve_memory_succeeds(self, agent_memory):
        """Test that an agent can store and retrieve memory.

        ReqID: N/A"""
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        memory_id = agent_memory.store_memory(memory_content, memory_type, metadata)
        assert memory_id is not None
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        assert retrieved_item.content == memory_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata["source"] == metadata["source"]
        assert retrieved_item.metadata["confidence"] == metadata["confidence"]
        assert retrieved_item.metadata["agent_name"] == "TestAgent"

    @pytest.mark.medium
    def test_agent_can_search_memory_succeeds(self, agent_memory):
        """Test that an agent can search memory.

        ReqID: N/A"""
        for i in range(5):
            memory_content = {"key": f"value{i}", "number": i}
            memory_type = MemoryType.KNOWLEDGE
            metadata = {"source": "test", "confidence": 0.9 - i * 0.1}
            agent_memory.store_memory(memory_content, memory_type, metadata)
        search_results = agent_memory.search_memory({"key": "value2"})
        assert len(search_results) == 1
        assert search_results[0].content["key"] == "value2"
        assert search_results[0].content["number"] == 2
        search_results = agent_memory.search_memory({"confidence": 0.9})
        assert len(search_results) == 1
        assert search_results[0].content["key"] == "value0"
        assert search_results[0].content["number"] == 0
        search_results = agent_memory.search_memory({"agent_name": "TestAgent"})
        assert len(search_results) == 5

    @pytest.mark.medium
    def test_agent_can_update_memory_succeeds(self, agent_memory):
        """Test that an agent can update memory.

        ReqID: N/A"""
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        memory_id = agent_memory.store_memory(memory_content, memory_type, metadata)
        updated_content = {"key": "updated_value", "number": 43}
        updated_metadata = {"source": "test", "confidence": 0.95}
        agent_memory.update_memory(memory_id, updated_content, updated_metadata)
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        assert retrieved_item.content == updated_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata["source"] == updated_metadata["source"]
        assert retrieved_item.metadata["confidence"] == updated_metadata["confidence"]
        assert retrieved_item.metadata["agent_name"] == "TestAgent"

    @pytest.mark.medium
    def test_agent_can_delete_memory_succeeds(self, agent_memory):
        """Test that an agent can delete memory.

        ReqID: N/A"""
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        memory_id = agent_memory.store_memory(memory_content, memory_type, metadata)
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        agent_memory.delete_memory(memory_id)
        retrieved_item = agent_memory.retrieve_memory(memory_id)
        assert retrieved_item is None

    @pytest.mark.medium
    def test_multiple_agents_can_share_memory_succeeds(self, memory_manager):
        """Test that multiple agents can share memory.

        ReqID: N/A"""
        agent1 = UnifiedAgent(
            name="Agent1",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"]),
        )
        agent2 = UnifiedAgent(
            name="Agent2",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"]),
        )
        agent1_memory = AgentMemoryIntegration(memory_manager, agent1)
        agent2_memory = AgentMemoryIntegration(memory_manager, agent2)
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9, "shared": True}
        memory_id = agent1_memory.store_memory(memory_content, memory_type, metadata)
        retrieved_item = agent2_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        assert retrieved_item.content == memory_content
        assert retrieved_item.memory_type == memory_type
        assert retrieved_item.metadata["source"] == metadata["source"]
        assert retrieved_item.metadata["confidence"] == metadata["confidence"]
        assert retrieved_item.metadata["agent_name"] == "Agent1"
        assert retrieved_item.metadata["shared"] == True

    @pytest.mark.medium
    def test_agent_memory_isolation_succeeds(self, memory_manager):
        """Test that agent memory can be isolated.

        ReqID: N/A"""
        agent1 = UnifiedAgent(
            name="Agent1",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"]),
        )
        agent2 = UnifiedAgent(
            name="Agent2",
            agent_type=AgentType.WSDE,
            config=AgentConfig(expertise=["testing", "memory"]),
        )
        agent1_memory = AgentMemoryIntegration(memory_manager, agent1)
        agent2_memory = AgentMemoryIntegration(memory_manager, agent2)
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9, "private": True}
        memory_id = agent1_memory.store_memory(memory_content, memory_type, metadata)
        retrieved_item = agent1_memory.retrieve_memory(memory_id)
        assert retrieved_item is not None
        retrieved_item = agent2_memory.retrieve_memory(memory_id)
        assert retrieved_item is None or retrieved_item.metadata.get("private") != True

    @pytest.mark.medium
    def test_agent_memory_with_context_succeeds(self, agent_memory):
        """Test that an agent can store and retrieve memory with context.

        ReqID: N/A"""
        memory_content = {"key": "value", "number": 42}
        memory_type = MemoryType.KNOWLEDGE
        metadata = {"source": "test", "confidence": 0.9}
        context = {"task_id": "task123", "phase": "testing"}
        memory_id = agent_memory.store_memory_with_context(
            memory_content, memory_type, metadata, context
        )
        assert memory_id is not None
        retrieved_items = agent_memory.retrieve_memory_with_context(context)
        assert len(retrieved_items) == 1
        assert retrieved_items[0].content == memory_content
        assert retrieved_items[0].memory_type == memory_type
        assert retrieved_items[0].metadata["source"] == metadata["source"]
        assert retrieved_items[0].metadata["confidence"] == metadata["confidence"]
        assert retrieved_items[0].metadata["agent_name"] == "TestAgent"

    @pytest.mark.requires_resource("lmdb")
    @pytest.mark.requires_resource("faiss")
    @pytest.mark.medium
    def test_persistent_sync_across_stores(self, tmp_path, monkeypatch):
        """Ensure LMDB and FAISS persistence with Kuzu resynchronization."""

        import sys

        LMDBStore = pytest.importorskip(
            "devsynth.application.memory.lmdb_store"
        ).LMDBStore
        FAISSStore = pytest.importorskip(
            "devsynth.application.memory.faiss_store"
        ).FAISSStore
        from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
        from devsynth.application.memory.kuzu_store import KuzuStore
        from devsynth.application.memory.sync_manager import SyncManager
        from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

        # Force use of the in-memory Kuzu fallback
        monkeypatch.delitem(sys.modules, "kuzu", raising=False)
        monkeypatch.setenv("DEVSYNTH_RESOURCE_KUZU_AVAILABLE", "false")

        ef = pytest.importorskip("chromadb.utils.embedding_functions")
        monkeypatch.setattr(
            ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5)
        )

        for cls in (LMDBStore, FAISSStore, KuzuMemoryStore, KuzuStore):
            try:
                monkeypatch.setattr(cls, "__abstractmethods__", frozenset())
            except Exception:
                pass

        lmdb_store = LMDBStore(str(tmp_path / "lmdb"))
        faiss_store = FAISSStore(str(tmp_path / "faiss"))
        kuzu_store = KuzuMemoryStore(
            persist_directory=str(tmp_path / "kuzu"), use_provider_system=False
        )

        manager = MemoryManager(
            adapters={"lmdb": lmdb_store, "faiss": faiss_store, "kuzu": kuzu_store}
        )
        manager.sync_manager = SyncManager(manager)

        item = MemoryItem(id="persist", content="data", memory_type=MemoryType.CODE)
        vector = MemoryVector(
            id="persist", content="data", embedding=[0.1] * 5, metadata={}
        )

        lmdb_store.store(item)
        faiss_store.store_vector(vector)
        manager.sync_manager.synchronize_core()

        assert kuzu_store.retrieve("persist") is not None
        assert kuzu_store.vector.retrieve_vector("persist") is not None

        # Simulate restart by creating new instances
        lmdb_store.close()
        lmdb2 = LMDBStore(str(tmp_path / "lmdb"))
        faiss2 = FAISSStore(str(tmp_path / "faiss"))
        kuzu2 = KuzuMemoryStore(
            persist_directory=str(tmp_path / "kuzu"), use_provider_system=False
        )

        manager2 = MemoryManager(
            adapters={"lmdb": lmdb2, "faiss": faiss2, "kuzu": kuzu2}
        )
        manager2.sync_manager = SyncManager(manager2)

        # LMDB and FAISS persisted
        assert lmdb2.retrieve("persist") is not None
        assert faiss2.retrieve_vector("persist") is not None
        # Kuzu fallback does not persist; synchronize to restore
        assert kuzu2.retrieve("persist") is None

        manager2.sync_manager.synchronize_core()

        assert kuzu2.retrieve("persist") is not None
        assert kuzu2.vector.retrieve_vector("persist") is not None

    @pytest.mark.medium
    def test_sync_manager_transaction_rolls_back_succeeds(self, temp_dir):
        """Ensure multi-store transactions roll back on error."""

        a = TinyDBMemoryAdapter(db_path=os.path.join(temp_dir, "a.json"))
        b = TinyDBMemoryAdapter(db_path=os.path.join(temp_dir, "b.json"))
        manager = MemoryManager(adapters={"a": a, "b": b})

        item = MemoryItem(id="t1", content="test", memory_type=MemoryType.KNOWLEDGE)

        with pytest.raises(RuntimeError):
            with manager.sync_manager.transaction(["a", "b"]):
                a.store(item)
                b.store(item)
                raise RuntimeError("fail")

        assert a.retrieve("t1") is None
        assert b.retrieve("t1") is None
