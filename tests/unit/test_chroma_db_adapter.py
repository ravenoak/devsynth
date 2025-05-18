
"""
Unit tests for the ChromaDBAdapter class.
"""
import os
import json
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from devsynth.domain.models.memory import MemoryVector
from devsynth.adapters.memory.chroma_db_adapter import ChromaDBAdapter
from devsynth.exceptions import MemoryStoreError


class TestChromaDBAdapter:
    """Test the ChromaDBAdapter class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up after the test
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def adapter(self, temp_dir):
        """Create a ChromaDBAdapter instance for testing."""
        return ChromaDBAdapter(persist_directory=temp_dir, collection_name="test_vectors")
    
    def test_initialization(self, temp_dir):
        """Test that the adapter initializes correctly."""
        adapter = ChromaDBAdapter(persist_directory=temp_dir, collection_name="test_vectors")
        assert adapter.persist_directory == temp_dir
        assert adapter.collection_name == "test_vectors"
        assert adapter.client is not None
        assert adapter.collection is not None
    
    def test_store_and_retrieve_vector(self, adapter):
        """Test storing and retrieving a vector."""
        # Create a test vector
        vector = MemoryVector(
            id="test-vector-1",
            content="This is a test vector",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"test": "metadata", "category": "test"}
        )
        
        # Store the vector
        vector_id = adapter.store_vector(vector)
        
        # Check that the ID is returned correctly
        assert vector_id == "test-vector-1"
        
        # Retrieve the vector
        retrieved_vector = adapter.retrieve_vector(vector_id)
        
        # Check that the retrieved vector matches the original
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector.id
        assert retrieved_vector.content == vector.content
        assert len(retrieved_vector.embedding) == len(vector.embedding)
        assert retrieved_vector.metadata["test"] == vector.metadata["test"]
        assert retrieved_vector.metadata["category"] == vector.metadata["category"]
    
    def test_store_vector_without_id(self, adapter):
        """Test storing a vector without an ID."""
        # Create a test vector without an ID
        vector = MemoryVector(
            id="",
            content="Vector without ID",
            embedding=[0.5, 0.4, 0.3, 0.2, 0.1],
            metadata={"test": "no-id"}
        )
        
        # Store the vector
        vector_id = adapter.store_vector(vector)
        
        # Check that an ID was generated
        assert vector_id is not None
        assert vector_id != ""
        
        # Retrieve the vector
        retrieved_vector = adapter.retrieve_vector(vector_id)
        
        # Check that the retrieved vector matches the original
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector_id
        assert retrieved_vector.content == vector.content
        assert retrieved_vector.metadata["test"] == vector.metadata["test"]
    
    def test_similarity_search(self, adapter):
        """Test similarity search functionality."""
        # Create and store test vectors
        vectors = [
            MemoryVector(
                id=f"test-vector-{i}",
                content=f"Test vector {i}",
                embedding=[float(j) / 10 for j in range(i, i + 5)],
                metadata={"index": i}
            )
            for i in range(1, 6)
        ]
        
        for vector in vectors:
            adapter.store_vector(vector)
        
        # Perform a similarity search
        query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55]  # Close to test-vector-2
        results = adapter.similarity_search(query_embedding, top_k=3)
        
        # Check that we got the expected number of results
        assert len(results) == 3
        
        # The closest vector should be test-vector-2
        # Note: This test might be flaky due to the nature of vector similarity
        # and the small test dataset, but it should generally work
        closest_ids = [v.id for v in results]
        assert "test-vector-2" in closest_ids
    
    def test_delete_vector(self, adapter):
        """Test deleting a vector."""
        # Create and store a test vector
        vector = MemoryVector(
            id="test-vector-delete",
            content="Vector to delete",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"test": "delete"}
        )
        
        adapter.store_vector(vector)
        
        # Delete the vector
        result = adapter.delete_vector(vector.id)
        
        # Check that the deletion was successful
        assert result is True
        
        # Try to retrieve the deleted vector
        retrieved_vector = adapter.retrieve_vector(vector.id)
        
        # Check that the vector is no longer available
        assert retrieved_vector is None
    
    def test_delete_nonexistent_vector(self, adapter):
        """Test deleting a vector that doesn't exist."""
        # Try to delete a non-existent vector
        result = adapter.delete_vector("nonexistent-vector")
        
        # Check that the deletion failed
        assert result is False
    
    def test_get_collection_stats(self, adapter):
        """Test getting collection statistics."""
        # Create and store test vectors
        vectors = [
            MemoryVector(
                id=f"stats-vector-{i}",
                content=f"Stats vector {i}",
                embedding=[float(j) / 10 for j in range(i, i + 5)],
                metadata={"index": i}
            )
            for i in range(1, 4)
        ]
        
        for vector in vectors:
            adapter.store_vector(vector)
        
        # Get collection statistics
        stats = adapter.get_collection_stats()
        
        # Check that the statistics are correct
        assert stats["collection_name"] == "test_vectors"
        assert stats["num_vectors"] >= 3  # At least the vectors we just added
        assert stats["embedding_dimension"] == 5
        assert stats["persist_directory"] == adapter.persist_directory
