import json
import os
import sys
import types
import uuid
from datetime import datetime, timedelta
from typing import Any, Protocol, TypeVar

import numpy as np
import pytest

pytestmark = pytest.mark.requires_resource("duckdb")


if "devsynth.core" not in sys.modules:
    core_stub = types.ModuleType("devsynth.core")

    class _FeatureFlags:
        @staticmethod
        def experimental_enabled() -> bool:
            return False

    core_stub.feature_flags = _FeatureFlags()  # type: ignore[attr-defined]
    sys.modules["devsynth.core"] = core_stub

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

sys.modules.pop("devsynth.application.memory.duckdb_store", None)

from devsynth.application.memory.dto import MemoryRecord, build_memory_record
from devsynth.application.memory.duckdb_store import DuckDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryStoreError


class TestDuckDBStore:
    """Tests for the DuckDBStore class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a DuckDBStore instance for testing."""
        store = DuckDBStore(temp_dir)
        store.vector_extension_available = False
        yield store
        if os.path.exists(os.path.join(temp_dir, "memory.duckdb")):
            os.remove(os.path.join(temp_dir, "memory.duckdb"))

    @pytest.mark.medium
    def test_init_succeeds(self, store, temp_dir):
        """Test initialization of DuckDBStore.

        ReqID: N/A"""
        assert store.base_path == temp_dir
        assert store.db_file == os.path.join(temp_dir, "memory.duckdb")
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
        store1 = DuckDBStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store1.store(item)
        store2 = DuckDBStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        record = build_memory_record(retrieved_item)
        assert isinstance(record, MemoryRecord)
        assert record.id == item_id
        assert record.content == "Test content"

    @pytest.mark.medium
    def test_store_vector_succeeds(self, store):
        """Test storing and retrieving a vector.

        ReqID: N/A"""
        vector = MemoryVector(
            id="",
            content="Test vector content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        vector_id = store.store_vector(vector)
        assert vector_id
        assert vector.id == vector_id
        retrieved_vector = store.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector_id
        assert retrieved_vector.content == "Test vector content"
        assert len(retrieved_vector.item.embedding) == 5
        assert np.allclose(retrieved_vector.item.embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
        assert retrieved_vector.metadata == {"key": "value"}
        assert isinstance(retrieved_vector.created_at, datetime)

    @pytest.mark.medium
    def test_similarity_search_succeeds(self, store):
        """Test similarity search for vectors.

        ReqID: N/A"""
        vectors = [
            MemoryVector(
                id="",
                content="Vector 1",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"key": "value1"},
                created_at=datetime.now(),
            ),
            MemoryVector(
                id="",
                content="Vector 2",
                embedding=[0.5, 0.4, 0.3, 0.2, 0.1],
                metadata={"key": "value2"},
                created_at=datetime.now(),
            ),
            MemoryVector(
                id="",
                content="Vector 3",
                embedding=[0.1, 0.1, 0.1, 0.1, 0.1],
                metadata={"key": "value3"},
                created_at=datetime.now(),
            ),
        ]
        for vector in vectors:
            store.store_vector(vector)
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = store.similarity_search(query_embedding, top_k=2)
        assert len(results) == 2
        assert results[0].content == "Vector 1"
        assert results[1].content in ["Vector 2", "Vector 3"]
        assert all(
            record.similarity is None or 0.0 <= record.similarity <= 1.0
            for record in results
        )

    @pytest.mark.medium
    def test_delete_vector_succeeds(self, store):
        """Test deleting a vector.

        ReqID: N/A"""
        vector = MemoryVector(
            id="",
            content="Test vector content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        vector_id = store.store_vector(vector)
        assert store.retrieve_vector(vector_id) is not None

        class _StubCursor:
            def __init__(self, rows):
                self._rows = rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

            def fetchall(self):
                return list(self._rows)

        original_execute = store.conn.execute

        def execute_wrapper(statement, params=None):
            normalized = " ".join(statement.strip().split())
            if normalized.startswith("SELECT id FROM memory_vectors WHERE id = ?"):
                if params == (vector_id,):
                    return _StubCursor([(vector_id,)])
                return _StubCursor([])
            return original_execute(statement, params)

        store.conn.execute = execute_wrapper

        try:
            result = store.delete_vector(vector_id)
            assert result is True
            assert store.retrieve_vector(vector_id) is None
            result = store.delete_vector("nonexistent")
            assert result is False
        finally:
            store.conn.execute = original_execute

    @pytest.mark.medium
    def test_get_collection_stats_succeeds(self, store):
        """Test getting collection statistics.

        ReqID: N/A"""

        class _StubCursor:
            def __init__(self, rows):
                self._rows = rows

            def fetchone(self):
                return self._rows[0] if self._rows else None

            def fetchall(self):
                return list(self._rows)

        first_responses = iter([_StubCursor([(0,)]), _StubCursor([]), _StubCursor([])])
        store.conn.execute = lambda *args, **kwargs: next(
            first_responses, _StubCursor([])
        )

        stats = store.get_collection_stats()
        assert stats["vector_count"] == 0

        second_responses = iter(
            [
                _StubCursor([(3,)]),
                _StubCursor(([json.dumps([0.1, 0.2, 0.3, 0.4, 0.5])],)),
                _StubCursor([]),
            ]
        )
        store.conn.execute = lambda *args, **kwargs: next(
            second_responses, _StubCursor([])
        )

        stats = store.get_collection_stats()
        assert stats["vector_count"] == 3
        assert stats["embedding_dimensions"] == 5

    @pytest.mark.medium
    def test_get_collection_stats_succeeds(self, store):
        """Test getting collection statistics.

        ReqID: N/A"""
