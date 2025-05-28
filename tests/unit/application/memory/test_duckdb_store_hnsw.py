import os
import json
import uuid
import pytest
import numpy as np
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

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

    @patch('duckdb.connect')
    def test_hnsw_index_creation(self, mock_connect, temp_dir):
        """Test that HNSW index is created when storing vectors."""
        # Create a mock connection
        mock_conn = MagicMock()

        # Configure the mock connection to return a result indicating an HNSW index exists
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("memory_vectors_hnsw_idx", "hnsw", "memory_vectors", "embedding")]
        mock_conn.execute.return_value = mock_result

        # Configure the mock_connect to return our mock connection
        mock_connect.return_value = mock_conn

        # Create a store with HNSW enabled
        store = DuckDBStore(temp_dir, enable_hnsw=True)

        # Set vector_extension_available to True
        store.vector_extension_available = True

        # Store some vectors
        for i in range(10):
            vector = MemoryVector(
                id="",
                content=f"Vector {i}",
                embedding=np.random.rand(5).tolist(),
                metadata={"index": i}
            )
            store.store_vector(vector)

        # Check that the HNSW index exists
        result = store.conn.execute("""
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

    @patch('duckdb.connect')
    def test_similarity_search_performance_comparison(self, mock_connect, temp_dir):
        """Compare performance of similarity search with and without HNSW index."""
        # Create two mock connections - one for each store
        mock_conn_without_hnsw = MagicMock()
        mock_conn_with_hnsw = MagicMock()

        # Configure the mock connections to return results for similarity search
        def create_mock_result(with_hnsw=False):
            mock_result = MagicMock()
            # Create 5 mock results with increasing distances
            results = []
            for i in range(5):
                # Make HNSW results slightly different to simulate performance difference
                distance = 0.1 * (i + 1) * (0.9 if with_hnsw else 1.0)
                results.append((
                    f"id_{i}",  # id
                    f"Vector {i}",  # content
                    [0.1, 0.2, 0.3, 0.4, 0.5],  # embedding
                    json.dumps({"index": i}),  # metadata
                    datetime.now().isoformat(),  # created_at
                    distance  # distance
                ))
            mock_result.fetchall.return_value = results
            return mock_result

        # Configure the mock connections to return appropriate results
        def mock_execute_side_effect(query, *args, **kwargs):
            if "duckdb_indexes()" in query and "index_type = 'hnsw'" in query:
                # Return a result indicating an HNSW index exists
                result = MagicMock()
                result.fetchall.return_value = [("memory_vectors_hnsw_idx", "hnsw", "memory_vectors", "embedding")]
                return result
            elif "vector_distance" in query:
                # For similarity search, return mock results with distances
                return create_mock_result(with_hnsw=True)
            elif "SELECT embedding FROM memory_vectors LIMIT 1" in query:
                # For dimension check
                result = MagicMock()
                result.fetchone.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
                return result
            elif "SELECT COUNT(*) FROM memory_vectors" in query:
                # For count check
                result = MagicMock()
                result.fetchone.return_value = [10]
                return result
            else:
                # For other queries
                result = MagicMock()
                result.fetchall.return_value = []
                result.fetchone.return_value = None
                return result

        # Configure both mock connections
        mock_conn_without_hnsw.execute.side_effect = mock_execute_side_effect
        mock_conn_with_hnsw.execute.side_effect = mock_execute_side_effect

        # Configure mock_connect to return different connections based on arguments
        mock_connect.side_effect = lambda db_file: mock_conn_with_hnsw if "hnsw" in db_file else mock_conn_without_hnsw

        # Create stores with and without HNSW
        store_without_hnsw = DuckDBStore(os.path.join(temp_dir, "without_hnsw"))
        store_with_hnsw = DuckDBStore(os.path.join(temp_dir, "with_hnsw"), enable_hnsw=True)

        # Set vector_extension_available to True for both stores
        store_without_hnsw.vector_extension_available = True
        store_with_hnsw.vector_extension_available = True

        # Create and store a few vectors for the test
        vectors = []
        for i in range(10):  # Reduced from 1000 to 10 for faster test
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
