import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pytest

pytest.importorskip("rdflib")
if os.environ.get("DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE", "true").lower() == "false":
    pytest.skip("RDFLib resource not available", allow_module_level=True)
from devsynth.application.memory.rdflib_store import RDFLibStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryStoreError

pytestmark = pytest.mark.requires_resource("rdflib")


class TestRDFLibStore:
    """Tests for the RDFLibStore class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a RDFLibStore instance for testing."""
        store = RDFLibStore(temp_dir)
        yield store
        if os.path.exists(os.path.join(temp_dir, "memory.ttl")):
            os.remove(os.path.join(temp_dir, "memory.ttl"))

    @pytest.mark.medium
    def test_init_succeeds(self, store, temp_dir):
        """Test initialization of RDFLibStore.

        ReqID: N/A"""
        assert store.base_path == temp_dir
        assert store.graph_file == os.path.join(temp_dir, "memory.ttl")
        assert store.token_count == 0
        assert len(store.graph) == 0

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
        assert len(results) == 2
        assert all((item.memory_type == MemoryType.SHORT_TERM for item in results))
        results = store.search({"metadata.tag": "test"})
        assert len(results) == 2
        assert all((item.metadata.get("tag") == "test" for item in results))
        results = store.search({"content": "Content 2"})
        assert len(results) == 1
        assert results[0].content == "Content 2"
        results = store.search(
            {"memory_type": MemoryType.SHORT_TERM, "metadata.tag": "test"}
        )
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SHORT_TERM
        assert results[0].metadata.get("tag") == "test"

    @pytest.mark.medium
    def test_search_by_id_and_date_range_succeeds(self, store):
        """Search using id and created_at range."""
        now = datetime.now()
        older = now - timedelta(days=1)
        items = [
            MemoryItem(
                id="a",
                content="One",
                memory_type=MemoryType.SHORT_TERM,
                metadata={},
                created_at=older,
            ),
            MemoryItem(
                id="b",
                content="Two",
                memory_type=MemoryType.SHORT_TERM,
                metadata={},
                created_at=now,
            ),
        ]
        for item in items:
            store.store(item)
        results = store.search({"id": "a"})
        assert len(results) == 1
        assert results[0].id == "a"
        results = store.search({"created_before": now})
        assert len(results) == 2
        results = store.search({"created_after": older})
        assert len(results) == 2

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
        store1 = RDFLibStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        item_id = store1.store(item)
        store2 = RDFLibStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"

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
        result = store.delete_vector(vector_id)
        assert result is True
        assert store.retrieve_vector(vector_id) is None
        result = store.delete_vector("nonexistent")
        assert result is False

    @pytest.mark.medium
    def test_get_collection_stats_succeeds(self, store):
        """Test getting collection statistics.

        ReqID: N/A"""
        stats = store.get_collection_stats()
        assert stats["vector_count"] == 0
        assert stats["num_triples"] == 0
        for i in range(3):
            vector = MemoryVector(
                id="",
                content=f"Vector {i}",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"index": i},
                created_at=datetime.now(),
            )
            store.store_vector(vector)
        stats = store.get_collection_stats()
        assert stats["vector_count"] == 3
        assert stats["embedding_dimensions"] == 5
        assert stats["num_triples"] > 0
