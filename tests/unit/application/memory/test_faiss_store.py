import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pytest

faiss = pytest.importorskip("faiss")
if os.environ.get("DEVSYNTH_RESOURCE_FAISS_AVAILABLE", "true").lower() == "false":
    pytest.skip("FAISS resource not available", allow_module_level=True)
from devsynth.application.memory.faiss_store import FAISSStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryStoreError

pytestmark = [
    pytest.mark.requires_resource("faiss"),
    pytest.mark.skip(
        reason="Skipping FAISS tests due to known issues with FAISS library"
    ),
]


class TestFAISSStore:
    """Tests for the FAISSStore class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a FAISSStore instance for testing."""
        store = FAISSStore(temp_dir)
        yield store
        if os.path.exists(os.path.join(temp_dir, "faiss_index.bin")):
            os.remove(os.path.join(temp_dir, "faiss_index.bin"))
        if os.path.exists(os.path.join(temp_dir, "metadata.json")):
            os.remove(os.path.join(temp_dir, "metadata.json"))

    @pytest.mark.medium
    def test_init_succeeds(self, store, temp_dir):
        """Test initialization of FAISSStore.

        ReqID: N/A"""
        assert store.base_path == temp_dir
        assert store.index_file == os.path.join(temp_dir, "faiss_index.bin")
        assert store.metadata_file == os.path.join(temp_dir, "metadata.json")
        assert store.token_count == 0
        assert store.index is not None
        assert isinstance(store.index, faiss.Index)

    @pytest.mark.medium
    def test_store_vector_succeeds(self, store):
        """Test storing a vector.

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
        assert len(retrieved_vector.embedding) == 5
        assert np.allclose(retrieved_vector.embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
        assert retrieved_vector.metadata == {"key": "value"}
        assert isinstance(retrieved_vector.created_at, datetime)

    @pytest.mark.medium
    def test_retrieve_vector_nonexistent_succeeds(self, store):
        """Test retrieving a nonexistent vector.

        ReqID: N/A"""
        retrieved_vector = store.retrieve_vector("nonexistent")
        assert retrieved_vector is None

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
        assert stats["num_vectors"] == 0
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
        assert stats["num_vectors"] == 3
        assert stats["embedding_dimension"] == 5

    @pytest.mark.medium
    def test_persistence_succeeds(self, temp_dir):
        """Test that data persists between store instances.

        ReqID: N/A"""
        store1 = FAISSStore(temp_dir)
        vector = MemoryVector(
            id="",
            content="Test vector content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"key": "value"},
            created_at=datetime.now(),
        )
        vector_id = store1.store_vector(vector)
        store2 = FAISSStore(temp_dir)
        retrieved_vector = store2.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector_id
        assert retrieved_vector.content == "Test vector content"
        assert np.allclose(retrieved_vector.embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
