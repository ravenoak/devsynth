"""
Unit tests for the MultiLayeredMemorySystem class.
"""

from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.memory.multi_layered_memory import MultiLayeredMemorySystem
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class TestMultiLayeredMemorySystem:
    """Tests for the MultiLayeredMemorySystem class.

    ReqID: N/A"""

    @pytest.fixture
    def memory_system(self):
        """Fixture that provides a MultiLayeredMemorySystem instance."""
        return MultiLayeredMemorySystem()

    @pytest.fixture
    def sample_memory_items(self):
        """Fixture that provides sample memory items for testing."""
        return {
            "context": MemoryItem(
                id="context-1",
                content="Current task context",
                memory_type=MemoryType.CONTEXT,
                metadata={"task_id": "task-123"},
            ),
            "conversation": MemoryItem(
                id="conversation-1",
                content="User conversation",
                memory_type=MemoryType.CONVERSATION,
                metadata={"user_id": "user-123"},
            ),
            "task_history": MemoryItem(
                id="task-history-1",
                content="Task execution history",
                memory_type=MemoryType.TASK_HISTORY,
                metadata={"task_id": "task-123"},
            ),
            "error_log": MemoryItem(
                id="error-log-1",
                content="Error occurred during execution",
                memory_type=MemoryType.ERROR_LOG,
                metadata={"error_code": "500"},
            ),
            "knowledge": MemoryItem(
                id="knowledge-1",
                content="Python best practices",
                memory_type=MemoryType.KNOWLEDGE,
                metadata={"category": "programming"},
            ),
            "documentation": MemoryItem(
                id="documentation-1",
                content="API documentation",
                memory_type=MemoryType.DOCUMENTATION,
                metadata={"api_version": "1.0"},
            ),
            "unknown": MemoryItem(
                id="unknown-1",
                content="Unknown memory type",
                memory_type="UNKNOWN",
                metadata={},
            ),
        }

    @pytest.mark.medium
    def test_init_succeeds(self, memory_system):
        """Test initialization of the MultiLayeredMemorySystem.

        ReqID: N/A"""
        assert memory_system.short_term_memory == {}
        assert memory_system.episodic_memory == {}
        assert memory_system.semantic_memory == {}
        assert memory_system.cache is None
        assert memory_system.cache_enabled is False
        assert memory_system.cache_stats == {"hits": 0, "misses": 0}

    @pytest.mark.medium
    def test_store_short_term_memory_succeeds(self, memory_system, sample_memory_items):
        """Test storing items in short-term memory.

        ReqID: N/A"""
        context_id = memory_system.store(sample_memory_items["context"])
        assert context_id == "context-1"
        assert context_id in memory_system.short_term_memory
        assert (
            memory_system.short_term_memory[context_id]
            == sample_memory_items["context"]
        )
        conversation_id = memory_system.store(sample_memory_items["conversation"])
        assert conversation_id == "conversation-1"
        assert conversation_id in memory_system.short_term_memory
        assert (
            memory_system.short_term_memory[conversation_id]
            == sample_memory_items["conversation"]
        )

    @pytest.mark.medium
    def test_store_episodic_memory_succeeds(self, memory_system, sample_memory_items):
        """Test storing items in episodic memory.

        ReqID: N/A"""
        task_history_id = memory_system.store(sample_memory_items["task_history"])
        assert task_history_id == "task-history-1"
        assert task_history_id in memory_system.episodic_memory
        assert (
            memory_system.episodic_memory[task_history_id]
            == sample_memory_items["task_history"]
        )
        error_log_id = memory_system.store(sample_memory_items["error_log"])
        assert error_log_id == "error-log-1"
        assert error_log_id in memory_system.episodic_memory
        assert (
            memory_system.episodic_memory[error_log_id]
            == sample_memory_items["error_log"]
        )

    @pytest.mark.medium
    def test_store_semantic_memory_succeeds(self, memory_system, sample_memory_items):
        """Test storing items in semantic memory.

        ReqID: N/A"""
        knowledge_id = memory_system.store(sample_memory_items["knowledge"])
        assert knowledge_id == "knowledge-1"
        assert knowledge_id in memory_system.semantic_memory
        assert (
            memory_system.semantic_memory[knowledge_id]
            == sample_memory_items["knowledge"]
        )
        documentation_id = memory_system.store(sample_memory_items["documentation"])
        assert documentation_id == "documentation-1"
        assert documentation_id in memory_system.semantic_memory
        assert (
            memory_system.semantic_memory[documentation_id]
            == sample_memory_items["documentation"]
        )

    @pytest.mark.medium
    def test_store_unknown_memory_type_succeeds(
        self, memory_system, sample_memory_items
    ):
        """Test storing items with unknown memory type.

        ReqID: N/A"""
        unknown_id = memory_system.store(sample_memory_items["unknown"])
        assert unknown_id == "unknown-1"
        assert unknown_id in memory_system.short_term_memory
        assert (
            memory_system.short_term_memory[unknown_id]
            == sample_memory_items["unknown"]
        )

    @pytest.mark.medium
    def test_store_without_id_succeeds(self, memory_system):
        """Test storing an item without an ID.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id=None,
            content="Item without ID",
            memory_type=MemoryType.CONTEXT,
            metadata={},
        )
        item_id = memory_system.store(memory_item)
        assert item_id is not None
        assert item_id == memory_item.id
        assert item_id in memory_system.short_term_memory

    @pytest.mark.medium
    def test_retrieve_succeeds(self, memory_system, sample_memory_items):
        """Test retrieving items from memory.

        ReqID: N/A"""
        context_id = memory_system.store(sample_memory_items["context"])
        task_history_id = memory_system.store(sample_memory_items["task_history"])
        knowledge_id = memory_system.store(sample_memory_items["knowledge"])
        context_item = memory_system.retrieve(context_id)
        task_history_item = memory_system.retrieve(task_history_id)
        knowledge_item = memory_system.retrieve(knowledge_id)
        assert context_item == sample_memory_items["context"]
        assert task_history_item == sample_memory_items["task_history"]
        assert knowledge_item == sample_memory_items["knowledge"]
        non_existent_item = memory_system.retrieve("non-existent-id")
        assert non_existent_item is None

    @pytest.mark.medium
    def test_retrieve_with_cache_succeeds(self, memory_system, sample_memory_items):
        """Test retrieving items with cache enabled.

        ReqID: N/A"""
        memory_system.enable_tiered_cache(max_size=10)
        item_id = memory_system.store(sample_memory_items["context"])
        item = memory_system.retrieve(item_id)
        assert item == sample_memory_items["context"]
        assert memory_system.cache_stats["hits"] == 0
        assert memory_system.cache_stats["misses"] == 1
        item = memory_system.retrieve(item_id)
        assert item == sample_memory_items["context"]
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1

    @pytest.mark.medium
    def test_store_preserves_typed_metadata(self, memory_system):
        """Stored items retain metadata mappings with supported value types.",

        ReqID: N/A"""

        metadata = {"score": 0.42, "tags": ["alpha", "beta"]}
        memory_item = MemoryItem(
            id="typed-1",
            content="Metadata aware",
            memory_type=MemoryType.CONTEXT,
            metadata=metadata,
        )

        item_id = memory_system.store(memory_item)
        retrieved = memory_system.retrieve(item_id)

        assert isinstance(retrieved.metadata, dict)
        assert retrieved.metadata is metadata
        assert isinstance(retrieved.metadata["tags"], list)
        assert retrieved.metadata["score"] == pytest.approx(0.42)

    @pytest.mark.medium
    def test_cache_round_trip_keeps_metadata_mapping(self, memory_system):
        """Cache hits should not alter metadata typing.",

        ReqID: N/A"""

        memory_system.enable_tiered_cache(max_size=5)
        metadata = {"count": 1, "details": {"phase": "EXPAND"}}
        memory_item = MemoryItem(
            id="cache-1",
            content="Cached",
            memory_type=MemoryType.CONVERSATION,
            metadata=metadata,
        )

        item_id = memory_system.store(memory_item)
        first = memory_system.retrieve(item_id)
        second = memory_system.retrieve(item_id)

        assert first is second
        assert isinstance(second.metadata, dict)
        assert isinstance(second.metadata["details"], dict)
        assert second.metadata["details"]["phase"] == "EXPAND"

    @pytest.mark.medium
    def test_query_returns_metadata_rich_items(
        self, memory_system, sample_memory_items
    ):
        """Layer queries yield items exposing typed metadata mappings.",

        ReqID: N/A"""

        for item in sample_memory_items.values():
            memory_system.store(item)

        semantic_items = memory_system.query({"layer": "semantic"})
        assert semantic_items
        for entry in semantic_items:
            assert isinstance(entry.metadata, dict)
            for value in entry.metadata.values():
                assert isinstance(
                    value, (str, int, float, bool, type(None), dict, list)
                )

    @pytest.mark.medium
    def test_get_items_by_layer_succeeds(self, memory_system, sample_memory_items):
        """Test getting items by layer.

        ReqID: N/A"""
        memory_system.store(sample_memory_items["context"])
        memory_system.store(sample_memory_items["conversation"])
        memory_system.store(sample_memory_items["task_history"])
        memory_system.store(sample_memory_items["error_log"])
        memory_system.store(sample_memory_items["knowledge"])
        memory_system.store(sample_memory_items["documentation"])
        short_term_items = memory_system.get_items_by_layer("short-term")
        episodic_items = memory_system.get_items_by_layer("episodic")
        semantic_items = memory_system.get_items_by_layer("semantic")
        assert len(short_term_items) == 2
        assert sample_memory_items["context"] in short_term_items
        assert sample_memory_items["conversation"] in short_term_items
        assert len(episodic_items) == 2
        assert sample_memory_items["task_history"] in episodic_items
        assert sample_memory_items["error_log"] in episodic_items
        assert len(semantic_items) == 2
        assert sample_memory_items["knowledge"] in semantic_items
        assert sample_memory_items["documentation"] in semantic_items
        unknown_layer_items = memory_system.get_items_by_layer("unknown-layer")
        assert unknown_layer_items == []

    @pytest.mark.medium
    def test_query_succeeds(self, memory_system, sample_memory_items):
        """Test querying memory items.

        ReqID: N/A"""
        memory_system.store(sample_memory_items["context"])
        memory_system.store(sample_memory_items["task_history"])
        memory_system.store(sample_memory_items["knowledge"])
        all_items = memory_system.query({})
        assert len(all_items) == 3
        assert sample_memory_items["context"] in all_items
        assert sample_memory_items["task_history"] in all_items
        assert sample_memory_items["knowledge"] in all_items
        short_term_items = memory_system.query({"layer": "short-term"})
        assert len(short_term_items) == 1
        assert sample_memory_items["context"] in short_term_items

    @pytest.mark.medium
    def test_tiered_cache_succeeds(self, memory_system):
        """Test tiered cache functionality.

        ReqID: N/A"""
        assert memory_system.is_tiered_cache_enabled() is False
        assert memory_system.get_cache_size() == 0
        assert memory_system.get_cache_max_size() == 0
        memory_system.enable_tiered_cache(max_size=10)
        assert memory_system.is_tiered_cache_enabled() is True
        assert memory_system.get_cache_size() == 0
        assert memory_system.get_cache_max_size() == 10
        memory_system.disable_tiered_cache()
        assert memory_system.is_tiered_cache_enabled() is False
        assert memory_system.get_cache_size() == 0
        assert memory_system.get_cache_max_size() == 0

    @pytest.mark.medium
    def test_clear_cache_succeeds(self, memory_system, sample_memory_items):
        """Test clearing the cache.

        ReqID: N/A"""
        memory_system.enable_tiered_cache(max_size=10)
        item_id = memory_system.store(sample_memory_items["context"])
        memory_system.retrieve(item_id)
        memory_system.retrieve(item_id)
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1
        memory_system.clear_cache()
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1
        memory_system.retrieve(item_id)
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 2

    @pytest.mark.medium
    def test_clear_succeeds(self, memory_system, sample_memory_items):
        """Test clearing all memory layers and cache.

        ReqID: N/A"""
        memory_system.store(sample_memory_items["context"])
        memory_system.store(sample_memory_items["task_history"])
        memory_system.store(sample_memory_items["knowledge"])
        memory_system.enable_tiered_cache(max_size=10)
        memory_system.retrieve(sample_memory_items["context"].id)
        memory_system.retrieve(sample_memory_items["context"].id)
        assert len(memory_system.short_term_memory) == 1
        assert len(memory_system.episodic_memory) == 1
        assert len(memory_system.semantic_memory) == 1
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1
        memory_system.clear()
        assert len(memory_system.short_term_memory) == 0
        assert len(memory_system.episodic_memory) == 0
        assert len(memory_system.semantic_memory) == 0
        assert memory_system.cache_stats["hits"] == 0
        assert memory_system.cache_stats["misses"] == 0
