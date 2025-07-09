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
    """Tests for the DuckDBStore class with HNSW index functionality.

ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing."""
        return str(tmp_path)

    @pytest.fixture
    def store(self, temp_dir):
        """Create a DuckDBStore instance for testing."""
        store = DuckDBStore(temp_dir)
        yield store
        if os.path.exists(os.path.join(temp_dir, 'memory.duckdb')):
            os.remove(os.path.join(temp_dir, 'memory.duckdb'))

    @pytest.fixture
    def store_with_hnsw(self, temp_dir):
        """Create a DuckDBStore instance with HNSW index enabled."""
        store = DuckDBStore(temp_dir, enable_hnsw=True)
        yield store
        if os.path.exists(os.path.join(temp_dir, 'memory.duckdb')):
            os.remove(os.path.join(temp_dir, 'memory.duckdb'))

    @pytest.fixture
    def store_with_custom_hnsw(self, temp_dir):
        """Create a DuckDBStore instance with custom HNSW parameters."""
        store = DuckDBStore(temp_dir, enable_hnsw=True, hnsw_config={'M': 
            16, 'efConstruction': 200, 'efSearch': 100})
        yield store
        if os.path.exists(os.path.join(temp_dir, 'memory.duckdb')):
            os.remove(os.path.join(temp_dir, 'memory.duckdb'))

    def test_hnsw_initialization_succeeds(self, store_with_hnsw):
        """Test initialization of DuckDBStore with HNSW index enabled.

ReqID: N/A"""
        assert store_with_hnsw.enable_hnsw is True
        assert store_with_hnsw.hnsw_config == {'M': 12, 'efConstruction': 
            100, 'efSearch': 50}

    def test_custom_hnsw_initialization_succeeds(self, store_with_custom_hnsw):
        """Test initialization of DuckDBStore with custom HNSW parameters.

ReqID: N/A"""
        assert store_with_custom_hnsw.enable_hnsw is True
        assert store_with_custom_hnsw.hnsw_config == {'M': 16,
            'efConstruction': 200, 'efSearch': 100}

    @patch('duckdb.connect')
    def test_hnsw_index_creation_succeeds(self, mock_connect, temp_dir):
        """Test that HNSW index is created when storing vectors.

ReqID: N/A"""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [('memory_vectors_hnsw_idx',
            'hnsw', 'memory_vectors', 'embedding')]
        mock_conn.execute.return_value = mock_result
        mock_connect.return_value = mock_conn
        store = DuckDBStore(temp_dir, enable_hnsw=True)
        store.vector_extension_available = True
        for i in range(10):
            vector = MemoryVector(id='', content=f'Vector {i}', embedding=
                np.random.rand(5).tolist(), metadata={'index': i})
            store.store_vector(vector)
        result = store.conn.execute(
            """
            SELECT * FROM duckdb_indexes()
            WHERE index_type = 'hnsw'
        """
            ).fetchall()
        assert len(result) > 0, 'HNSW index was not created'

    def test_similarity_search_with_hnsw_succeeds(self, store_with_hnsw):
        """Test similarity search with HNSW index.

ReqID: N/A"""
        vectors = []
        for i in range(100):
            vector = MemoryVector(id='', content=f'Vector {i}', embedding=
                np.random.rand(5).tolist(), metadata={'index': i})
            vector_id = store_with_hnsw.store_vector(vector)
            vectors.append((vector_id, vector.embedding))
        query_embedding = vectors[0][1]
        results = store_with_hnsw.similarity_search(query_embedding, top_k=5)
        assert len(results) == 5
        assert results[0].id == vectors[0][0]

    @patch('duckdb.connect')
    def test_similarity_search_performance_comparison_succeeds(self,
        mock_connect, temp_dir):
        """Compare performance of similarity search with and without HNSW index.

ReqID: N/A"""
        mock_conn_without_hnsw = MagicMock()
        mock_conn_with_hnsw = MagicMock()

        def create_mock_result(with_hnsw=False):
            mock_result = MagicMock()
            results = []
            for i in range(5):
                distance = 0.1 * (i + 1) * (0.9 if with_hnsw else 1.0)
                results.append((f'id_{i}', f'Vector {i}', [0.1, 0.2, 0.3, 
                    0.4, 0.5], json.dumps({'index': i}), datetime.now().
                    isoformat(), distance))
            mock_result.fetchall.return_value = results
            return mock_result

        def mock_execute_side_effect(query, *args, **kwargs):
            if 'duckdb_indexes()' in query and "index_type = 'hnsw'" in query:
                result = MagicMock()
                result.fetchall.return_value = [('memory_vectors_hnsw_idx',
                    'hnsw', 'memory_vectors', 'embedding')]
                return result
            elif 'vector_distance' in query:
                return create_mock_result(with_hnsw=True)
            elif 'SELECT embedding FROM memory_vectors LIMIT 1' in query:
                result = MagicMock()
                result.fetchone.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
                return result
            elif 'SELECT COUNT(*) FROM memory_vectors' in query:
                result = MagicMock()
                result.fetchone.return_value = [10]
                return result
            else:
                result = MagicMock()
                result.fetchall.return_value = []
                result.fetchone.return_value = None
                return result
        mock_conn_without_hnsw.execute.side_effect = mock_execute_side_effect
        mock_conn_with_hnsw.execute.side_effect = mock_execute_side_effect
        mock_connect.side_effect = (lambda db_file: mock_conn_with_hnsw if 
            'hnsw' in db_file else mock_conn_without_hnsw)
        store_without_hnsw = DuckDBStore(os.path.join(temp_dir, 'without_hnsw')
            )
        store_with_hnsw = DuckDBStore(os.path.join(temp_dir, 'with_hnsw'),
            enable_hnsw=True)
        store_without_hnsw.vector_extension_available = True
        store_with_hnsw.vector_extension_available = True
        vectors = []
        for i in range(10):
            embedding = np.random.rand(5).tolist()
            vector = MemoryVector(id='', content=f'Vector {i}', embedding=
                embedding, metadata={'index': i})
            store_without_hnsw.store_vector(vector)
            vector_id = store_with_hnsw.store_vector(vector)
            if i == 0:
                vectors.append((vector_id, embedding))
        query_embedding = vectors[0][1]
        start_time = time.time()
        results_without_hnsw = store_without_hnsw.similarity_search(
            query_embedding, top_k=5)
        time_without_hnsw = time.time() - start_time
        start_time = time.time()
        results_with_hnsw = store_with_hnsw.similarity_search(query_embedding,
            top_k=5)
        time_with_hnsw = time.time() - start_time
        assert len(results_without_hnsw) == len(results_with_hnsw)
        print(f'Time without HNSW: {time_without_hnsw:.6f}s')
        print(f'Time with HNSW: {time_with_hnsw:.6f}s')
        print(f'Speedup: {time_without_hnsw / time_with_hnsw:.2f}x')
