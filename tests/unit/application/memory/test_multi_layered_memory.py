"""
Unit tests for the MultiLayeredMemorySystem class.
"""

import pytest
from unittest.mock import patch, MagicMock

from devsynth.application.memory.multi_layered_memory import MultiLayeredMemorySystem
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


class TestMultiLayeredMemorySystem:
    """Tests for the MultiLayeredMemorySystem class."""

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
                metadata={"task_id": "task-123"}
            ),
            "conversation": MemoryItem(
                id="conversation-1",
                content="User conversation",
                memory_type=MemoryType.CONVERSATION,
                metadata={"user_id": "user-123"}
            ),
            "task_history": MemoryItem(
                id="task-history-1",
                content="Task execution history",
                memory_type=MemoryType.TASK_HISTORY,
                metadata={"task_id": "task-123"}
            ),
            "error_log": MemoryItem(
                id="error-log-1",
                content="Error occurred during execution",
                memory_type=MemoryType.ERROR_LOG,
                metadata={"error_code": "500"}
            ),
            "knowledge": MemoryItem(
                id="knowledge-1",
                content="Python best practices",
                memory_type=MemoryType.KNOWLEDGE,
                metadata={"category": "programming"}
            ),
            "documentation": MemoryItem(
                id="documentation-1",
                content="API documentation",
                memory_type=MemoryType.DOCUMENTATION,
                metadata={"api_version": "1.0"}
            ),
            "unknown": MemoryItem(
                id="unknown-1",
                content="Unknown memory type",
                memory_type="UNKNOWN",
                metadata={}
            )
        }

    def test_init(self, memory_system):
        """Test initialization of the MultiLayeredMemorySystem."""
        assert memory_system.short_term_memory == {}
        assert memory_system.episodic_memory == {}
        assert memory_system.semantic_memory == {}
        assert memory_system.cache is None
        assert memory_system.cache_enabled is False
        assert memory_system.cache_stats == {"hits": 0, "misses": 0}

    def test_store_short_term_memory(self, memory_system, sample_memory_items):
        """Test storing items in short-term memory."""
        # Store context item
        context_id = memory_system.store(sample_memory_items["context"])
        assert context_id == "context-1"
        assert context_id in memory_system.short_term_memory
        assert memory_system.short_term_memory[context_id] == sample_memory_items["context"]

        # Store conversation item
        conversation_id = memory_system.store(sample_memory_items["conversation"])
        assert conversation_id == "conversation-1"
        assert conversation_id in memory_system.short_term_memory
        assert memory_system.short_term_memory[conversation_id] == sample_memory_items["conversation"]

    def test_store_episodic_memory(self, memory_system, sample_memory_items):
        """Test storing items in episodic memory."""
        # Store task history item
        task_history_id = memory_system.store(sample_memory_items["task_history"])
        assert task_history_id == "task-history-1"
        assert task_history_id in memory_system.episodic_memory
        assert memory_system.episodic_memory[task_history_id] == sample_memory_items["task_history"]

        # Store error log item
        error_log_id = memory_system.store(sample_memory_items["error_log"])
        assert error_log_id == "error-log-1"
        assert error_log_id in memory_system.episodic_memory
        assert memory_system.episodic_memory[error_log_id] == sample_memory_items["error_log"]

    def test_store_semantic_memory(self, memory_system, sample_memory_items):
        """Test storing items in semantic memory."""
        # Store knowledge item
        knowledge_id = memory_system.store(sample_memory_items["knowledge"])
        assert knowledge_id == "knowledge-1"
        assert knowledge_id in memory_system.semantic_memory
        assert memory_system.semantic_memory[knowledge_id] == sample_memory_items["knowledge"]

        # Store documentation item
        documentation_id = memory_system.store(sample_memory_items["documentation"])
        assert documentation_id == "documentation-1"
        assert documentation_id in memory_system.semantic_memory
        assert memory_system.semantic_memory[documentation_id] == sample_memory_items["documentation"]

    def test_store_unknown_memory_type(self, memory_system, sample_memory_items):
        """Test storing items with unknown memory type."""
        # Store unknown item (should default to short-term memory)
        unknown_id = memory_system.store(sample_memory_items["unknown"])
        assert unknown_id == "unknown-1"
        assert unknown_id in memory_system.short_term_memory
        assert memory_system.short_term_memory[unknown_id] == sample_memory_items["unknown"]

    def test_store_without_id(self, memory_system):
        """Test storing an item without an ID."""
        # Create a memory item with ID set to None
        memory_item = MemoryItem(
            id=None,
            content="Item without ID",
            memory_type=MemoryType.CONTEXT,
            metadata={}
        )

        # Store the item
        item_id = memory_system.store(memory_item)

        # Verify that an ID was generated
        assert item_id is not None
        assert item_id == memory_item.id
        assert item_id in memory_system.short_term_memory

    def test_retrieve(self, memory_system, sample_memory_items):
        """Test retrieving items from memory."""
        # Store items in different memory layers
        context_id = memory_system.store(sample_memory_items["context"])
        task_history_id = memory_system.store(sample_memory_items["task_history"])
        knowledge_id = memory_system.store(sample_memory_items["knowledge"])

        # Retrieve items from different memory layers
        context_item = memory_system.retrieve(context_id)
        task_history_item = memory_system.retrieve(task_history_id)
        knowledge_item = memory_system.retrieve(knowledge_id)

        # Verify retrieved items
        assert context_item == sample_memory_items["context"]
        assert task_history_item == sample_memory_items["task_history"]
        assert knowledge_item == sample_memory_items["knowledge"]

        # Try to retrieve a non-existent item
        non_existent_item = memory_system.retrieve("non-existent-id")
        assert non_existent_item is None

    def test_retrieve_with_cache(self, memory_system, sample_memory_items):
        """Test retrieving items with cache enabled."""
        # Enable cache
        memory_system.enable_tiered_cache(max_size=10)

        # Store an item
        item_id = memory_system.store(sample_memory_items["context"])

        # Retrieve the item (should be a cache miss)
        item = memory_system.retrieve(item_id)
        assert item == sample_memory_items["context"]
        assert memory_system.cache_stats["hits"] == 0
        assert memory_system.cache_stats["misses"] == 1

        # Retrieve the item again (should be a cache hit)
        item = memory_system.retrieve(item_id)
        assert item == sample_memory_items["context"]
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1

    def test_get_items_by_layer(self, memory_system, sample_memory_items):
        """Test getting items by layer."""
        # Store items in different memory layers
        memory_system.store(sample_memory_items["context"])
        memory_system.store(sample_memory_items["conversation"])
        memory_system.store(sample_memory_items["task_history"])
        memory_system.store(sample_memory_items["error_log"])
        memory_system.store(sample_memory_items["knowledge"])
        memory_system.store(sample_memory_items["documentation"])

        # Get items by layer
        short_term_items = memory_system.get_items_by_layer("short-term")
        episodic_items = memory_system.get_items_by_layer("episodic")
        semantic_items = memory_system.get_items_by_layer("semantic")

        # Verify items by layer
        assert len(short_term_items) == 2
        assert sample_memory_items["context"] in short_term_items
        assert sample_memory_items["conversation"] in short_term_items

        assert len(episodic_items) == 2
        assert sample_memory_items["task_history"] in episodic_items
        assert sample_memory_items["error_log"] in episodic_items

        assert len(semantic_items) == 2
        assert sample_memory_items["knowledge"] in semantic_items
        assert sample_memory_items["documentation"] in semantic_items

        # Try to get items from an unknown layer
        unknown_layer_items = memory_system.get_items_by_layer("unknown-layer")
        assert unknown_layer_items == []

    def test_query(self, memory_system, sample_memory_items):
        """Test querying memory items."""
        # Store items in different memory layers
        memory_system.store(sample_memory_items["context"])
        memory_system.store(sample_memory_items["task_history"])
        memory_system.store(sample_memory_items["knowledge"])

        # Query all layers
        all_items = memory_system.query({})
        assert len(all_items) == 3
        assert sample_memory_items["context"] in all_items
        assert sample_memory_items["task_history"] in all_items
        assert sample_memory_items["knowledge"] in all_items

        # Query specific layer
        short_term_items = memory_system.query({"layer": "short-term"})
        assert len(short_term_items) == 1
        assert sample_memory_items["context"] in short_term_items

    def test_tiered_cache(self, memory_system):
        """Test tiered cache functionality."""
        # Initially, cache should be disabled
        assert memory_system.is_tiered_cache_enabled() is False
        assert memory_system.get_cache_size() == 0
        assert memory_system.get_cache_max_size() == 0

        # Enable cache
        memory_system.enable_tiered_cache(max_size=10)
        assert memory_system.is_tiered_cache_enabled() is True
        assert memory_system.get_cache_size() == 0
        assert memory_system.get_cache_max_size() == 10

        # Disable cache
        memory_system.disable_tiered_cache()
        assert memory_system.is_tiered_cache_enabled() is False
        assert memory_system.get_cache_size() == 0
        assert memory_system.get_cache_max_size() == 0

    def test_clear_cache(self, memory_system, sample_memory_items):
        """Test clearing the cache."""
        # Enable cache
        memory_system.enable_tiered_cache(max_size=10)

        # Store and retrieve an item to populate the cache
        item_id = memory_system.store(sample_memory_items["context"])
        memory_system.retrieve(item_id)
        memory_system.retrieve(item_id)

        # Verify cache stats
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1

        # Clear cache
        memory_system.clear_cache()

        # Cache stats should remain unchanged
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1

        # Retrieve the item again (should be a cache miss)
        memory_system.retrieve(item_id)
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 2

    def test_clear(self, memory_system, sample_memory_items):
        """Test clearing all memory layers and cache."""
        # Store items in different memory layers
        memory_system.store(sample_memory_items["context"])
        memory_system.store(sample_memory_items["task_history"])
        memory_system.store(sample_memory_items["knowledge"])

        # Enable cache
        memory_system.enable_tiered_cache(max_size=10)

        # Retrieve items to populate the cache
        memory_system.retrieve(sample_memory_items["context"].id)
        memory_system.retrieve(sample_memory_items["context"].id)

        # Verify memory layers and cache stats
        assert len(memory_system.short_term_memory) == 1
        assert len(memory_system.episodic_memory) == 1
        assert len(memory_system.semantic_memory) == 1
        assert memory_system.cache_stats["hits"] == 1
        assert memory_system.cache_stats["misses"] == 1

        # Clear all memory layers and cache
        memory_system.clear()

        # Verify memory layers and cache stats are cleared
        assert len(memory_system.short_term_memory) == 0
        assert len(memory_system.episodic_memory) == 0
        assert len(memory_system.semantic_memory) == 0
        assert memory_system.cache_stats["hits"] == 0
        assert memory_system.cache_stats["misses"] == 0
