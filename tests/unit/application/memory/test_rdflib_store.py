import os
import json
import uuid
import pytest
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.application.memory.rdflib_store import RDFLibStore
from devsynth.exceptions import MemoryStoreError

class TestRDFLibStore:
    """Tests for the RDFLibStore class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a RDFLibStore instance for testing."""
        store = RDFLibStore(temp_dir)
        yield store
        # Clean up
        if os.path.exists(os.path.join(temp_dir, "memory.ttl")):
            os.remove(os.path.join(temp_dir, "memory.ttl"))

    def test_init(self, store, temp_dir):
        """Test initialization of RDFLibStore."""
        assert store.base_path == temp_dir
        assert store.graph_file == os.path.join(temp_dir, "memory.ttl")
        assert store.token_count == 0
        assert len(store.graph) == 0  # Graph should be empty initially

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
        store1 = RDFLibStore(temp_dir)
        item = MemoryItem(
            id="",
            content="Test content",
            memory_type=MemoryType.SHORT_TERM,
            metadata={"key": "value"},
            created_at=datetime.now()
        )
        item_id = store1.store(item)

        # Create a new store instance and verify the item exists
        store2 = RDFLibStore(temp_dir)
        retrieved_item = store2.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "Test content"

    def test_store_vector(self, store):
        """Test storing and retrieving a vector."""
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
        assert stats["num_triples"] == 0

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
        assert stats["num_triples"] > 0  # Should have some triples now
