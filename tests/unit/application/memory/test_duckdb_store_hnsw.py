import os
import json
import uuid
import pytest
import numpy as np
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.application.memory.duckdb_store import DuckDBStore
from devsynth.exceptions import MemoryStoreError

class TestDuckDBStoreHNSW:
    """Tests for the DuckDBStore class with HNSW index functionality."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a DuckDBStore instance for testing."""
        store = DuckDBStore(temp_dir)
        yield store
        # Clean up
        if os.path.exists(os.path.join(temp_dir, "memory.duckdb")):
            os.remove(os.path.join(temp_dir, "memory.duckdb"))

    @pytest.fixture
    def store_with_hnsw(self, temp_dir):
        """Create a DuckDBStore instance with HNSW index enabled."""
        store = DuckDBStore(temp_dir, enable_hnsw=True)
        yield store
        # Clean up
        if os.path.exists(os.path.join(temp_dir, "memory.duckdb")):
            os.remove(os.path.join(temp_dir, "memory.duckdb"))

    @pytest.fixture
    def store_with_custom_hnsw(self, temp_dir):
        """Create a DuckDBStore instance with custom HNSW parameters."""
        store = DuckDBStore(
            temp_dir,
            enable_hnsw=True,
            hnsw_config={
                "M": 16,
                "efConstruction": 200,
                "efSearch": 100
            }
        )
        yield store
        # Clean up
        if os.path.exists(os.path.join(temp_dir, "memory.duckdb")):
            os.remove(os.path.join(temp_dir, "memory.duckdb"))

    def test_hnsw_initialization(self, store_with_hnsw):
        """Test initialization of DuckDBStore with HNSW index enabled."""
        assert store_with_hnsw.enable_hnsw is True
        assert store_with_hnsw.hnsw_config == {
            "M": 12,  # Default value
            "efConstruction": 100,  # Default value
            "efSearch": 50  # Default value
        }

    def test_custom_hnsw_initialization(self, store_with_custom_hnsw):
        """Test initialization of DuckDBStore with custom HNSW parameters."""
        assert store_with_custom_hnsw.enable_hnsw is True
        assert store_with_custom_hnsw.hnsw_config == {
            "M": 16,
            "efConstruction": 200,
            "efSearch": 100
        }

    def test_hnsw_index_creation(self, store_with_hnsw):
        """Test that HNSW index is created when storing vectors."""
        # Store some vectors
        for i in range(10):
            vector = MemoryVector(
                id="",
                content=f"Vector {i}",
                embedding=np.random.rand(5).tolist(),
                metadata={"index": i}
            )
            store_with_hnsw.store_vector(vector)

        # Skip this test if vector extension is not available
        if not store_with_hnsw.vector_extension_available:
            pytest.skip("Vector extension not available, skipping HNSW index test")

        # Check that the HNSW index exists
        result = store_with_hnsw.conn.execute("""
            SELECT * FROM duckdb_indexes()
            WHERE index_type = 'hnsw'
        """).fetchall()

        assert len(result) > 0, "HNSW index was not created"

    def test_similarity_search_with_hnsw(self, store_with_hnsw):
        """Test similarity search with HNSW index."""
        # Create and store vectors
        vectors = []
        for i in range(100):  # Store more vectors to see performance difference
            vector = MemoryVector(
                id="",
                content=f"Vector {i}",
                embedding=np.random.rand(5).tolist(),
                metadata={"index": i}
            )
            vector_id = store_with_hnsw.store_vector(vector)
            vectors.append((vector_id, vector.embedding))

        # Pick a random vector for search
        query_embedding = vectors[0][1]

        # Perform search
        results = store_with_hnsw.similarity_search(query_embedding, top_k=5)

        # Verify results
        assert len(results) == 5
        assert results[0].id == vectors[0][0]  # First result should be the query vector itself

    def test_similarity_search_performance_comparison(self, temp_dir):
        """Compare performance of similarity search with and without HNSW index."""
        # Create stores with and without HNSW
        store_without_hnsw = DuckDBStore(temp_dir)
        store_with_hnsw = DuckDBStore(temp_dir, enable_hnsw=True)

        # Skip this test if vector extension is not available
        if not store_with_hnsw.vector_extension_available:
            pytest.skip("Vector extension not available, skipping performance comparison test")

        # Create and store vectors in both stores
        vectors = []
        for i in range(1000):  # Store many vectors to see performance difference
            embedding = np.random.rand(5).tolist()
            vector = MemoryVector(
                id="",
                content=f"Vector {i}",
                embedding=embedding,
                metadata={"index": i}
            )
            store_without_hnsw.store_vector(vector)
            vector_id = store_with_hnsw.store_vector(vector)
            if i == 0:
                vectors.append((vector_id, embedding))

        # Pick the first vector for search
        query_embedding = vectors[0][1]

        # Measure time for search without HNSW
        start_time = time.time()
        results_without_hnsw = store_without_hnsw.similarity_search(query_embedding, top_k=5)
        time_without_hnsw = time.time() - start_time

        # Measure time for search with HNSW
        start_time = time.time()
        results_with_hnsw = store_with_hnsw.similarity_search(query_embedding, top_k=5)
        time_with_hnsw = time.time() - start_time

        # Verify both searches return the same number of results
        assert len(results_without_hnsw) == len(results_with_hnsw)

        # Log performance difference
        print(f"Time without HNSW: {time_without_hnsw:.6f}s")
        print(f"Time with HNSW: {time_with_hnsw:.6f}s")
        print(f"Speedup: {time_without_hnsw / time_with_hnsw:.2f}x")

        # We expect HNSW to be faster, but this might not always be true for small datasets
        # So we don't assert on the actual performance, just log it
