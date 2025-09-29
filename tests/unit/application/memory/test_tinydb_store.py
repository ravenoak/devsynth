import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

pytest.importorskip("tinydb")
if os.environ.get("DEVSYNTH_RESOURCE_TINYDB_AVAILABLE", "true").lower() == "false":
    pytest.skip("TinyDB resource not available", allow_module_level=True)
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.application.memory.dto import build_memory_record
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError

pytestmark = pytest.mark.requires_resource("tinydb")


class TestTinyDBStore:
    """Tests for the TinyDBStore class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a TinyDBStore instance for testing."""
        store = TinyDBStore(temp_dir)
        yield store
        if os.path.exists(os.path.join(temp_dir, "memory.json")):
            os.remove(os.path.join(temp_dir, "memory.json"))

    @pytest.mark.medium
    def test_init_succeeds(self, store, temp_dir):
        """Test initialization of TinyDBStore.

        ReqID: N/A"""
        assert store.base_path == temp_dir
        assert store.db_file == os.path.join(temp_dir, "memory.json")
        assert store.token_count == 0

    @pytest.mark.medium
    def test_store_and_retrieve_succeeds(self, store):
        """Test storing and retrieving a memory item.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store.store(item)
        assert item_id
        assert item.id == item_id
        retrieved_item = store.retrieve(item_id)
        assert retrieved_item is not None
        assert isinstance(retrieved_item, MemoryItem)
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"
        assert retrieved_item.memory_type == MemoryType.SHORT_TERM
        assert retrieved_item.metadata == {"key": "value"}
        assert isinstance(retrieved_item.created_at, datetime)

    @pytest.mark.medium
    def test_retrieve_nonexistent_succeeds(self, store):
        """Test retrieving a nonexistent memory item.

        ReqID: N/A"""
        retrieved_item = store.retrieve("nonexistent")
        assert retrieved_item is None

    @pytest.mark.medium
    def test_search_succeeds(self, store):
        """Test searching for memory items.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id="",
                content="Content 1",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value1", "tag": "test"},
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Content 2",
                memory_type=MemoryType.LONG_TERM,
                metadata={"key": "value2", "tag": "test"},
                created_at=datetime.now(),
            ),
            MemoryItem(
                id="",
                content="Content 3",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value3", "tag": "other"},
                created_at=datetime.now(),
            ),
        ]
        for item in items:
            store.store(item)
        results = store.search({"memory_type": MemoryType.SHORT_TERM})
        assert isinstance(results, list)
        assert all(isinstance(item, MemoryItem) for item in results)
        assert all(isinstance(build_memory_record(item).metadata, dict) for item in results)
        assert len(results) == 2
        assert all((item.memory_type == MemoryType.SHORT_TERM for item in results))
        results = store.search({"metadata.tag": "test"})
        assert isinstance(results, list)
        assert all(isinstance(item, MemoryItem) for item in results)
        assert all(isinstance(build_memory_record(item).metadata, dict) for item in results)
        assert len(results) == 2
        assert all((item.metadata.get("tag") == "test" for item in results))
        results = store.search({"content": "Content 2"})
        assert isinstance(results, list)
        assert all(isinstance(item, MemoryItem) for item in results)
        assert all(isinstance(build_memory_record(item).metadata, dict) for item in results)
        assert len(results) == 1
        assert results[0].content == "Content 2"
        results = store.search(
            {"memory_type": MemoryType.SHORT_TERM, "metadata.tag": "test"}
        )
        assert isinstance(results, list)
        assert all(isinstance(item, MemoryItem) for item in results)
        assert all(isinstance(build_memory_record(item).metadata, dict) for item in results)
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SHORT_TERM
        assert results[0].metadata.get("tag") == "test"

    @pytest.mark.medium
    def test_delete_succeeds(self, store):
        """Test deleting a memory item.

        ReqID: N/A"""
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store.store(item)
        assert store.retrieve(item_id) is not None
        result = store.delete(item_id)
        assert result is True
        assert store.retrieve(item_id) is None
        result = store.delete("nonexistent")
        assert result is False

    @pytest.mark.medium
    def test_token_usage_succeeds(self, store):
        """Test token usage tracking.

        ReqID: N/A"""
        assert store.get_token_usage() == 0
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        store.store(item)
        assert store.get_token_usage() > 0
        store.retrieve(item.id)
        assert store.get_token_usage() > 0

    @pytest.mark.medium
    def test_persistence_succeeds(self, temp_dir):
        """Test that data persists between store instances.

        ReqID: N/A"""
        store1 = TinyDBStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store1.store(item)
        store1.close()
        store2 = TinyDBStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"
        store2.close()
