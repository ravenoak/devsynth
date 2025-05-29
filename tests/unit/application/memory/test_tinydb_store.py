import os
import json
import uuid
import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.exceptions import MemoryStoreError

class TestTinyDBStore:
    """Tests for the TinyDBStore class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a TinyDBStore instance for testing."""
        store = TinyDBStore(temp_dir)
        yield store
        # Clean up
        if os.path.exists(os.path.join(temp_dir, "memory.json")):
            os.remove(os.path.join(temp_dir, "memory.json"))

    def test_init(self, store, temp_dir):
        """Test initialization of TinyDBStore."""
        assert store.base_path == temp_dir
        assert store.db_file == os.path.join(temp_dir, "memory.json")
        assert store.token_count == 0

    def test_store_and_retrieve(self, store):
        """Test storing and retrieving a memory item."""
        # Create a memory item
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )

        # Store the item
        item_id = store.store(item)

        # Verify the ID was assigned
        assert item_id
        assert item.id == item_id

        # Retrieve the item
        retrieved_item = store.retrieve(item_id)

        # Verify the retrieved item matches the original
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"
        assert retrieved_item.memory_type == MemoryType.SHORT_TERM
        assert retrieved_item.metadata == {"key": "value"}
        assert isinstance(retrieved_item.created_at, datetime)

    def test_retrieve_nonexistent(self, store):
        """Test retrieving a nonexistent memory item."""
        retrieved_item = store.retrieve("nonexistent")
        assert retrieved_item is None

    def test_search(self, store):
        """Test searching for memory items."""
        # Create and store memory items
        items = [
            MemoryItem(
                id="",
                content="Content 1",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value1", "tag": "test"},
                created_at=datetime.now()
            ),
            MemoryItem(
                id="",
                content="Content 2",
                memory_type=MemoryType.LONG_TERM,
                metadata={"key": "value2", "tag": "test"},
                created_at=datetime.now()
            ),
            MemoryItem(
                id="",
                content="Content 3",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value3", "tag": "other"},
                created_at=datetime.now()
            )
        ]

        for item in items:
            store.store(item)

        # Search by memory_type
        results = store.search({"memory_type": MemoryType.SHORT_TERM})
        assert len(results) == 2
        assert all(item.memory_type == MemoryType.SHORT_TERM for item in results)

        # Search by metadata
        results = store.search({"metadata.tag": "test"})
        assert len(results) == 2
        assert all(item.metadata.get("tag") == "test" for item in results)

        # Search by content
        results = store.search({"content": "Content 2"})
        assert len(results) == 1
        assert results[0].content == "Content 2"

        # Combined search
        results = store.search({
            "memory_type": MemoryType.SHORT_TERM,
            "metadata.tag": "test"
        })
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SHORT_TERM
        assert results[0].metadata.get("tag") == "test"

    def test_delete(self, store):
        """Test deleting a memory item."""
        # Create and store a memory item
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        item_id = store.store(item)

        # Verify the item exists
        assert store.retrieve(item_id) is not None

        # Delete the item
        result = store.delete(item_id)
        assert result is True

        # Verify the item no longer exists
        assert store.retrieve(item_id) is None

        # Try to delete a nonexistent item
        result = store.delete("nonexistent")
        assert result is False

    def test_token_usage(self, store):
        """Test token usage tracking."""
        # Initial token count should be 0
        assert store.get_token_usage() == 0

        # Store an item
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        store.store(item)

        # Token count should be greater than 0
        assert store.get_token_usage() > 0

        # Retrieve the item
        store.retrieve(item.id)

        # Token count should increase
        assert store.get_token_usage() > 0

    def test_persistence(self, temp_dir):
        """Test that data persists between store instances."""
        # Create a store and add an item
        store1 = TinyDBStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        item_id = store1.store(item)

        # Explicitly close the first store to ensure data is persisted
        store1.close()

        # Create a new store instance and verify the item exists
        store2 = TinyDBStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"

        # Clean up
        store2.close()
