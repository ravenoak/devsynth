import os
import json
import uuid
import pytest
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.application.memory.lmdb_store import LMDBStore
from devsynth.exceptions import MemoryStoreError

class TestLMDBStore:
    """Tests for the LMDBStore class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a LMDBStore instance for testing."""
        store = LMDBStore(temp_dir)
        yield store
        # Clean up
        store.close()
        if os.path.exists(os.path.join(temp_dir, "memory.lmdb")):
            shutil.rmtree(os.path.join(temp_dir, "memory.lmdb"))

    def test_init(self, store, temp_dir):
        """Test initialization of LMDBStore."""
        assert store.base_path == temp_dir
        assert store.db_path == os.path.join(temp_dir, "memory.lmdb")
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
        store1 = LMDBStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        item_id = store1.store(item)
        store1.close()

        # Create a new store instance and verify the item exists
        store2 = LMDBStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"
        store2.close()

    def test_close_and_reopen(self, store, temp_dir):
        """Test closing and reopening the store."""
        # Store an item
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        item_id = store.store(item)

        # Close the store
        store.close()

        # Reopen the store
        store = LMDBStore(temp_dir)

        # Verify the item exists
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"

    def test_transaction_isolation(self, store):
        """Test that transactions are isolated."""
        # Store an item in a transaction
        with store.begin_transaction() as txn:
            item = MemoryItem(
                id="",
                content="Transaction test",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value"},
                created_at=datetime.now()
            )
            item_id = store.store_in_transaction(txn, item)

            # Item should be visible within the transaction
            retrieved_item = store.retrieve_in_transaction(txn, item_id)
            assert retrieved_item is not None
            assert retrieved_item.content == "Transaction test"

        # Item should be visible after the transaction is committed
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == "Transaction test"

    def test_transaction_abort(self, store):
        """Test that aborted transactions don't persist changes."""
        # Store an item outside a transaction
        item1 = MemoryItem(
            id="",
            content="Outside transaction",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value1"},
            created_at=datetime.now()
        )
        item1_id = store.store(item1)

        # Start a transaction but abort it
        try:
            with store.begin_transaction() as txn:
                # Store a new item in the transaction
                item2 = MemoryItem(
                    id="",
                    content="Inside transaction",
                    memory_type=MemoryType.SHORT_TERM,
                    metadata={"key": "value2"},
                    created_at=datetime.now()
                )
                item2_id = store.store_in_transaction(txn, item2)

                # Modify the existing item in the transaction
                item1.content = "Modified in transaction"
                store.store_in_transaction(txn, item1)

                # Items should be visible within the transaction
                assert store.retrieve_in_transaction(txn, item1_id).content == "Modified in transaction"
                assert store.retrieve_in_transaction(txn, item2_id) is not None

                # Abort the transaction by raising an exception
                raise ValueError("Abort transaction")
        except ValueError:
            pass

        # The new item should not exist
        assert store.retrieve(item2_id) is None

        # The existing item should not be modified
        assert store.retrieve(item1_id).content == "Outside transaction"
