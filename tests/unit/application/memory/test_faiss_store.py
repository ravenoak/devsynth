import os
import json
import uuid
import numpy as np
try:
    import faiss
except ImportError:  # pragma: no cover - optional dependency
    faiss = None
import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.application.memory.faiss_store import FAISSStore
from devsynth.exceptions import MemoryStoreError

# Skip all tests in this file to avoid fatal Python errors
pytestmark = [
    pytest.mark.requires_resource("faiss"),
    pytest.mark.skip(reason="Skipping FAISS tests due to known issues with FAISS library")
]

class TestFAISSStore:
    """Tests for the FAISSStore class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a FAISSStore instance for testing."""
        store = FAISSStore(temp_dir)
        yield store
        # Clean up
        if os.path.exists(os.path.join(temp_dir, "faiss_index.bin")):
            os.remove(os.path.join(temp_dir, "faiss_index.bin"))
        if os.path.exists(os.path.join(temp_dir, "metadata.json")):
            os.remove(os.path.join(temp_dir, "metadata.json"))

    def test_init(self, store, temp_dir):
        """Test initialization of FAISSStore."""
        assert store.base_path == temp_dir
        assert store.index_file == os.path.join(temp_dir, "faiss_index.bin")
        assert store.metadata_file == os.path.join(temp_dir, "metadata.json")
        assert store.token_count == 0
        assert store.index is not None
        assert isinstance(store.index, faiss.Index)

    def test_store_vector(self, store):
        """Test storing a vector."""
        # Create a memory vector
        vector = MemoryVector(
            id="",
            content="Test vector content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"key": "value"},
            created_at=datetime.now()
        )

        # Store the vector
        vector_id = store.store_vector(vector)

        # Verify the ID was assigned
        assert vector_id
        assert vector.id == vector_id

        # Retrieve the vector
        retrieved_vector = store.retrieve_vector(vector_id)

        # Verify the retrieved vector matches the original
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector_id
        assert retrieved_vector.content == "Test vector content"
        assert len(retrieved_vector.embedding) == 5
        assert np.allclose(retrieved_vector.embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
        assert retrieved_vector.metadata == {"key": "value"}
        assert isinstance(retrieved_vector.created_at, datetime)

    def test_retrieve_vector_nonexistent(self, store):
        """Test retrieving a nonexistent vector."""
        retrieved_vector = store.retrieve_vector("nonexistent")
        assert retrieved_vector is None

    def test_similarity_search(self, store):
        """Test similarity search for vectors."""
        # Create and store vectors
        vectors = [
            MemoryVector(
                id="",
                content="Vector 1",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"key": "value1"},
                created_at=datetime.now()
            ),
            MemoryVector(
                id="",
                content="Vector 2",
                embedding=[0.5, 0.4, 0.3, 0.2, 0.1],
                metadata={"key": "value2"},
                created_at=datetime.now()
            ),
            MemoryVector(
                id="",
                content="Vector 3",
                embedding=[0.1, 0.1, 0.1, 0.1, 0.1],
                metadata={"key": "value3"},
                created_at=datetime.now()
            )
        ]

        for vector in vectors:
            store.store_vector(vector)

        # Search for similar vectors
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        results = store.similarity_search(query_embedding, top_k=2)

        # Verify the results
        assert len(results) == 2
        # The first result should be the most similar (Vector 1)
        assert results[0].content == "Vector 1"
        # The second result should be the second most similar
        assert results[1].content in ["Vector 2", "Vector 3"]

    def test_delete_vector(self, store):
        """Test deleting a vector."""
        # Create and store a vector
        vector = MemoryVector(
            id="",
            content="Test vector content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        vector_id = store.store_vector(vector)

        # Verify the vector exists
        assert store.retrieve_vector(vector_id) is not None

        # Delete the vector
        result = store.delete_vector(vector_id)
        assert result is True

        # Verify the vector no longer exists
        assert store.retrieve_vector(vector_id) is None

        # Try to delete a nonexistent vector
        result = store.delete_vector("nonexistent")
        assert result is False

    def test_get_collection_stats(self, store):
        """Test getting collection statistics."""
        # Initially, the collection should be empty
        stats = store.get_collection_stats()
        assert stats["num_vectors"] == 0

        # Add some vectors
        for i in range(3):
            vector = MemoryVector(
                id="",
                content=f"Vector {i}",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"index": i},
                created_at=datetime.now()
            )
            store.store_vector(vector)

        # Get updated stats
        stats = store.get_collection_stats()
        assert stats["num_vectors"] == 3
        assert stats["embedding_dimension"] == 5

    def test_persistence(self, temp_dir):
        """Test that data persists between store instances."""
        # Create a store and add a vector
        store1 = FAISSStore(temp_dir)
        vector = MemoryVector(
            id="",
            content="Test vector content",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        vector_id = store1.store_vector(vector)

        # Create a new store instance and verify the vector exists
        store2 = FAISSStore(temp_dir)
        retrieved_vector = store2.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector_id
        assert retrieved_vector.content == "Test vector content"
        assert np.allclose(retrieved_vector.embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
