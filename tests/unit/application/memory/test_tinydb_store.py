import json
import os
import sys
import types
import uuid
from datetime import datetime, timedelta
from typing import Any, Protocol, TypeVar

import pytest

pytestmark = pytest.mark.requires_resource("tinydb")


pytest.importorskip("tinydb")
if os.environ.get("DEVSYNTH_RESOURCE_TINYDB_AVAILABLE", "true").lower() == "false":
    pytest.skip("TinyDB resource not available", allow_module_level=True)
sys.modules.pop("devsynth.domain.interfaces.memory", None)
interfaces_pkg = sys.modules.setdefault(
    "devsynth.domain.interfaces", types.ModuleType("devsynth.domain.interfaces")
)
memory_stub = types.ModuleType("devsynth.domain.interfaces.memory")

MemorySearchResponse = list[Any]


class _MemoryStore(Protocol):
    def store(self, item): ...

    def retrieve(self, item_id): ...

    def search(self, query): ...

    def delete(self, item_id): ...

    def begin_transaction(self): ...

    def commit_transaction(self, transaction_id): ...

    def rollback_transaction(self, transaction_id): ...

    def is_transaction_active(self, transaction_id): ...


_VectorT = TypeVar("_VectorT")


class _VectorStore(Protocol[_VectorT]):
    def store_vector(self, vector): ...

    def retrieve_vector(self, vector_id): ...

    def similarity_search(self, query_embedding, top_k=5): ...

    def delete_vector(self, vector_id): ...

    def get_collection_stats(self): ...


class _ContextManager(Protocol):
    def add_to_context(self, key, value): ...

    def get_from_context(self, key): ...

    def get_full_context(self): ...

    def clear_context(self): ...


class _SupportsTransactions(Protocol):
    def begin_transaction(self): ...

    def commit_transaction(self, transaction_id): ...

    def rollback_transaction(self, transaction_id): ...

    def is_transaction_active(self, transaction_id): ...


memory_stub.MemoryStore = _MemoryStore  # type: ignore[attr-defined]
memory_stub.VectorStore = _VectorStore  # type: ignore[attr-defined]
memory_stub.ContextManager = _ContextManager  # type: ignore[attr-defined]
memory_stub.SupportsTransactions = _SupportsTransactions  # type: ignore[attr-defined]
memory_stub.MemorySearchResponse = MemorySearchResponse  # type: ignore[attr-defined]
sys.modules["devsynth.domain.interfaces.memory"] = memory_stub
setattr(interfaces_pkg, "memory", memory_stub)

sys.modules.pop("devsynth.application.memory.tinydb_store", None)

from devsynth.application.memory.dto import MemoryRecord, build_memory_record
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError


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
        record = build_memory_record(retrieved_item)
        assert isinstance(record, MemoryRecord)
        assert record.id == item_id
        assert record.content == "Test content"
        assert record.memory_type == MemoryType.SHORT_TERM
        assert record.item.metadata == {"key": "value"}
        assert isinstance(record.created_at, datetime)

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
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert all(isinstance(record.metadata, dict) for record in results)
        assert len(results) == 2
        assert all(
            record.item.memory_type == MemoryType.SHORT_TERM for record in results
        )
        results = store.search({"metadata.tag": "test"})
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert all(isinstance(record.metadata, dict) for record in results)
        assert len(results) == 2
        assert all((record.metadata or {}).get("tag") == "test" for record in results)
        results = store.search({"content": "Content 2"})
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert all(isinstance(record.metadata, dict) for record in results)
        assert len(results) == 1
        assert results[0].content == "Content 2"
        results = store.search(
            {"memory_type": MemoryType.SHORT_TERM, "metadata.tag": "test"}
        )
        assert isinstance(results, list)
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert all(isinstance(record.metadata, dict) for record in results)
        assert len(results) == 1
        assert results[0].item.memory_type == MemoryType.SHORT_TERM
        assert (results[0].metadata or {}).get("tag") == "test"

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
        record = build_memory_record(retrieved_item)
        assert isinstance(record, MemoryRecord)
        assert record.id == item_id
        assert record.content == "Test content"
        store2.close()
