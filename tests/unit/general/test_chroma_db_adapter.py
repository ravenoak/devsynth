"""
Unit tests for the ChromaDBAdapter class.
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from devsynth.adapters.memory.chroma_db_adapter import ChromaDBAdapter
from devsynth.domain.models.memory import MemoryVector
from devsynth.exceptions import MemoryStoreError


class TestChromaDBAdapter:
    """Test the ChromaDBAdapter class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def adapter(self, temp_dir):
        """Create a ChromaDBAdapter instance for testing."""
        return ChromaDBAdapter(
            persist_directory=temp_dir, collection_name="test_vectors"
        )

    @pytest.mark.fast
    def test_initialization_succeeds(self, temp_dir):
        """Test that the adapter initializes correctly.

        ReqID: N/A"""
        adapter = ChromaDBAdapter(
            persist_directory=temp_dir, collection_name="test_vectors"
        )
        assert adapter.persist_directory == temp_dir
        assert adapter.collection_name == "test_vectors"
        assert adapter.client is not None
        assert adapter.collection is not None

    @pytest.mark.fast
    def test_store_and_retrieve_vector_succeeds(self, adapter):
        """Test storing and retrieving a vector.

        ReqID: N/A"""
        vector = MemoryVector(
            id="test-vector-1",
            content="This is a test vector",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"test": "metadata", "category": "test"},
        )
        vector_id = adapter.store_vector(vector)
        assert vector_id == "test-vector-1"
        retrieved_vector = adapter.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector.id
        assert retrieved_vector.content == vector.content
        assert len(retrieved_vector.embedding) == len(vector.embedding)
        assert retrieved_vector.metadata["test"] == vector.metadata["test"]
        assert retrieved_vector.metadata["category"] == vector.metadata["category"]

    @pytest.mark.fast
    def test_store_vector_without_id_succeeds(self, adapter):
        """Test storing a vector without an ID.

        ReqID: N/A"""
        vector = MemoryVector(
            id="",
            content="Vector without ID",
            embedding=[0.5, 0.4, 0.3, 0.2, 0.1],
            metadata={"test": "no-id"},
        )
        vector_id = adapter.store_vector(vector)
        assert vector_id is not None
        assert vector_id != ""
        retrieved_vector = adapter.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.id == vector_id
        assert retrieved_vector.content == vector.content
        assert retrieved_vector.metadata["test"] == vector.metadata["test"]

    @pytest.mark.fast
    def test_similarity_search_succeeds(self, adapter):
        """Test similarity search functionality.

        ReqID: N/A"""
        vectors = [
            MemoryVector(
                id=f"test-vector-{i}",
                content=f"Test vector {i}",
                embedding=[(float(j) / 10) for j in range(i, i + 5)],
                metadata={"index": i},
            )
            for i in range(1, 6)
        ]
        for vector in vectors:
            adapter.store_vector(vector)
        query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55]
        results = adapter.similarity_search(query_embedding, top_k=3)
        assert len(results) == 3
        closest_ids = [v.id for v in results]
        assert "test-vector-2" in closest_ids

    @pytest.mark.fast
    def test_delete_vector_succeeds(self, adapter):
        """Test deleting a vector.

        ReqID: N/A"""
        vector = MemoryVector(
            id="test-vector-delete",
            content="Vector to delete",
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"test": "delete"},
        )
        adapter.store_vector(vector)
        result = adapter.delete_vector(vector.id)
        assert result is True
        retrieved_vector = adapter.retrieve_vector(vector.id)
        assert retrieved_vector is None

    @pytest.mark.fast
    def test_delete_nonexistent_vector_succeeds(self, adapter):
        """Test deleting a vector that doesn't exist.

        ReqID: N/A"""
        result = adapter.delete_vector("nonexistent-vector")
        assert result is False

    @pytest.mark.fast
    def test_get_collection_stats_succeeds(self, adapter):
        """Test getting collection statistics.

        ReqID: N/A"""
        vectors = [
            MemoryVector(
                id=f"stats-vector-{i}",
                content=f"Stats vector {i}",
                embedding=[(float(j) / 10) for j in range(i, i + 5)],
                metadata={"index": i},
            )
            for i in range(1, 4)
        ]
        for vector in vectors:
            adapter.store_vector(vector)
        stats = adapter.get_collection_stats()
        assert stats["collection_name"] == "test_vectors"
        assert stats["vector_count"] >= 3
        assert stats["embedding_dimensions"] == 5
        assert stats["persist_directory"] == adapter.persist_directory
