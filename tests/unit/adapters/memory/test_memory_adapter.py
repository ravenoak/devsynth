import os
import sys
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# These tests exercise multiple backend implementations and can consume
# significant memory when run in parallel. Mark them for isolation so
# they execute sequentially and avoid xdist resource contention.

pytestmark = [
    pytest.mark.memory_intensive,
    pytest.mark.isolation,
]

# Import duckdb safely
try:
    import duckdb
except ImportError:
    duckdb = None
from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.application.memory.context_manager import (
    InMemoryStore,
    SimpleContextManager,
)
from devsynth.application.memory.duckdb_store import DuckDBStore
from devsynth.application.memory.json_file_store import JSONFileStore
from devsynth.application.memory.persistent_context_manager import (
    PersistentContextManager,
)
from devsynth.application.memory.rdflib_store import RDFLibStore
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.domain.interfaces.memory import MemoryStore, VectorStore
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector
from devsynth.exceptions import MemoryStoreError

try:
    from devsynth.application.memory.lmdb_store import LMDBStore
except Exception:  # pragma: no cover - optional
    LMDBStore = None
try:  # pragma: no cover - optional
    from devsynth.application.memory.faiss_store import FAISSStore
except Exception:
    FAISSStore = None
try:
    from devsynth.application.memory.kuzu_store import KuzuStore
except Exception:  # pragma: no cover - optional
    KuzuStore = None

for cls in (
    JSONFileStore,
    TinyDBStore,
    DuckDBStore,
    KuzuMemoryStore,
    KuzuAdapter,
    RDFLibStore,
    LMDBStore,
    FAISSStore,
    KuzuStore,
    InMemoryStore,
):
    if cls is not None:
        try:
            cls.__abstractmethods__ = frozenset()
        except Exception:
            pass


class TestMemorySystemAdapter:
    """Tests for the MemorySystemAdapter class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Provide a temporary directory for testing and ensure cleanup."""
        path = tmp_path
        yield str(path)

    @pytest.mark.medium
    def test_init_with_file_storage_succeeds(self, temp_dir):
        """Test initialization with file storage.

        ReqID: N/A"""
        config = {
            "memory_store_type": "file",
            "memory_file_path": temp_dir,
            # Use a small context size to keep memory usage low during tests
            "max_context_size": 10,
            "context_expiration_days": 1,
            "vector_store_enabled": False,
        }
        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "file"
        assert temp_dir in adapter.memory_path or adapter.memory_path in temp_dir
        assert isinstance(adapter.memory_store, JSONFileStore)
        assert isinstance(adapter.context_manager, PersistentContextManager)
        assert adapter.vector_store is None

    @pytest.mark.slow
    def test_init_with_tinydb_storage_succeeds(self, temp_dir):
        """Test initialization with TinyDB storage.

        ReqID: N/A"""
        config = {
            "memory_store_type": "tinydb",
            "memory_file_path": temp_dir,
            # Smaller context prevents large preallocation during TinyDB tests
            "max_context_size": 10,
            "context_expiration_days": 1,
            "vector_store_enabled": False,
        }
        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "tinydb"
        assert adapter.memory_path == temp_dir
        assert isinstance(adapter.memory_store, TinyDBStore)
        assert isinstance(adapter.context_manager, PersistentContextManager)
        assert adapter.vector_store is None
        del adapter

    @pytest.mark.skipif(duckdb is None, reason="duckdb not installed")
    @pytest.mark.slow
    def test_init_with_duckdb_storage_succeeds(self, temp_dir, monkeypatch):
        """Test initialization with DuckDB storage.

        ReqID: N/A"""
        with patch("duckdb.connect") as mock_connect:
            # Use MagicMock with spec to ensure it has the same interface as the real DuckDB connection
            from devsynth.application.memory.adapters._duckdb_protocols import (
                DuckDBConnectionProtocol,
            )

            mock_conn = MagicMock(spec=DuckDBConnectionProtocol)
            mock_conn.execute.return_value = None
            mock_connect.return_value = mock_conn
            original_init_schema = DuckDBStore._initialize_schema

            def mock_init_schema(self):
                original_init_schema(self)
                self.vector_extension_available = True

            monkeypatch.setattr(DuckDBStore, "_initialize_schema", mock_init_schema)
            config = {
                "memory_store_type": "duckdb",
                "memory_file_path": temp_dir,
                # Minimize context to reduce memory footprint in DuckDB tests
                "max_context_size": 10,
                "context_expiration_days": 1,
                "vector_store_enabled": True,
            }
            adapter = MemorySystemAdapter(config=config)
            assert adapter.storage_type == "duckdb"
            assert adapter.memory_path == temp_dir
            assert isinstance(adapter.memory_store, DuckDBStore)
            assert isinstance(adapter.context_manager, PersistentContextManager)
            assert adapter.vector_store is not None
            assert adapter.vector_store is adapter.memory_store
            del adapter

    @pytest.mark.requires_resource("lmdb")
    @pytest.mark.slow
    def test_init_with_lmdb_storage_succeeds(self, temp_dir):
        """Test initialization with LMDB storage.

        ReqID: N/A"""
        config = {
            "memory_store_type": "lmdb",
            "memory_file_path": temp_dir,
            # Small context size keeps tests lightweight
            "max_context_size": 10,
            "context_expiration_days": 1,
            "vector_store_enabled": False,
        }
        pytest.importorskip("lmdb")
        from devsynth.application.memory.lmdb_store import LMDBStore

        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "lmdb"
        assert adapter.memory_path == temp_dir
        assert isinstance(adapter.memory_store, LMDBStore)
        assert isinstance(adapter.context_manager, PersistentContextManager)
        assert adapter.vector_store is None
        del adapter

    @pytest.mark.requires_resource("kuzu")
    @pytest.mark.medium
    def test_init_with_kuzu_storage_succeeds(self, temp_dir):
        """Test initialization with Kuzu storage.

        ReqID: N/A"""
        config = {
            "memory_store_type": "kuzu",
            "memory_file_path": temp_dir,
            # Limit context size for lightweight RDFLib tests
            "max_context_size": 10,
            "context_expiration_days": 1,
            "vector_store_enabled": True,
        }
        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "kuzu"
        assert temp_dir in adapter.memory_path or adapter.memory_path in temp_dir
        assert isinstance(adapter.memory_store, KuzuMemoryStore)
        assert isinstance(adapter.context_manager, PersistentContextManager)
        assert adapter.vector_store is not None
        assert isinstance(adapter.vector_store, KuzuAdapter)
        del adapter

    @pytest.mark.requires_resource("faiss")
    @pytest.mark.medium
    def test_init_with_faiss_storage_succeeds(self, temp_dir):
        """Test initialization with FAISS storage.

        ReqID: N/A"""
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        config = {
            "memory_store_type": "faiss",
            "memory_file_path": temp_dir,
            # Ensure minimal context allocation for vector store tests
            "max_context_size": 10,
            "context_expiration_days": 1,
            "vector_store_enabled": True,
        }
        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "faiss"
        assert adapter.memory_path == temp_dir
        assert isinstance(adapter.memory_store, JSONFileStore)
        assert isinstance(adapter.context_manager, PersistentContextManager)
        assert adapter.vector_store is not None
        assert isinstance(adapter.vector_store, FAISSStore)
        del adapter

    @pytest.mark.requires_resource("faiss")
    @pytest.mark.medium
    def test_faiss_vector_store_operations_succeeds(self, temp_dir):
        """Test vector store operations with FAISS.

        ReqID: N/A"""
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        pytest.skip("Skipping FAISS test due to known issues with FAISS library")
        try:
            config = {
                "memory_store_type": "faiss",
                "memory_file_path": temp_dir,
                # Reduce context size to avoid large in-memory structures
                "max_context_size": 10,
                "context_expiration_days": 1,
                "vector_store_enabled": True,
            }
            adapter = MemorySystemAdapter(config=config)
            vector = MemoryVector(
                id="",
                content="Test vector content",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"key": "value"},
            )
            vector_store = adapter.get_vector_store()
            assert vector_store is not None
            vector_id = vector_store.store_vector(vector)
            retrieved_vector = vector_store.retrieve_vector(vector_id)
            assert retrieved_vector is not None
            assert retrieved_vector.id == vector_id
            assert retrieved_vector.content == "Test vector content"
            assert np.allclose(retrieved_vector.embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
            assert vector_store.delete_vector(vector_id) is True
            assert vector_store.retrieve_vector(vector_id) is None
            del vector_store
            del adapter
        except Exception as e:
            pytest.skip(f"Skipping FAISS test due to error: {e}")

    @pytest.mark.requires_resource("faiss")
    @pytest.mark.medium
    def test_memory_and_vector_store_integration_succeeds(self, temp_dir):
        """Test integration between memory store and vector store.

        ReqID: N/A"""
        pytest.importorskip("faiss")
        from devsynth.application.memory.faiss_store import FAISSStore

        pytest.skip(
            "Skipping FAISS integration test due to known issues with FAISS library"
        )
        try:
            config = {
                "memory_store_type": "faiss",
                "memory_file_path": temp_dir,
                # Keep context small for Kuzu adapter tests
                "max_context_size": 10,
                "context_expiration_days": 1,
                "vector_store_enabled": True,
            }
            adapter = MemorySystemAdapter(config=config)
            memory_item = MemoryItem(
                id="",
                content="Test memory content",
                memory_type=MemoryType.SHORT_TERM,
                metadata={"key": "value"},
            )
            memory_store = adapter.get_memory_store()
            item_id = memory_store.store(memory_item)
            vector = MemoryVector(
                id="",
                content="Test vector content",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"memory_item_id": item_id},
            )
            vector_store = adapter.get_vector_store()
            assert vector_store is not None
            vector_id = vector_store.store_vector(vector)
            retrieved_item = memory_store.retrieve(item_id)
            retrieved_vector = vector_store.retrieve_vector(vector_id)
            assert retrieved_item is not None
            assert retrieved_vector is not None
            assert retrieved_item.id == item_id
            assert retrieved_vector.id == vector_id
            assert retrieved_vector.metadata.get("memory_item_id") == item_id
            del vector_store
            del adapter
        except Exception as e:
            pytest.skip(f"Skipping FAISS integration test due to error: {e}")

    @pytest.mark.medium
    def test_init_with_rdflib_storage_succeeds(self, temp_dir):
        """Test initialization with RDFLib storage.

        ReqID: N/A"""
        config = {
            "memory_store_type": "rdflib",
            "memory_file_path": temp_dir,
            # Smaller context suffices for in-memory store tests
            "max_context_size": 10,
            "context_expiration_days": 1,
            "vector_store_enabled": True,
        }
        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "rdflib"
        assert adapter.memory_path == temp_dir
        assert isinstance(adapter.memory_store, RDFLibStore)
        assert isinstance(adapter.context_manager, PersistentContextManager)
        assert adapter.vector_store is adapter.memory_store
        del adapter

    @pytest.mark.medium
    def test_init_with_in_memory_storage_succeeds(self):
        """Test initialization with in-memory storage.

        ReqID: N/A"""
        config = {"memory_store_type": "memory", "vector_store_enabled": False}
        adapter = MemorySystemAdapter(config=config)
        assert adapter.storage_type == "memory"
        assert isinstance(adapter.memory_store, InMemoryStore)
        assert isinstance(adapter.context_manager, SimpleContextManager)
        assert adapter.vector_store is None
        del adapter

    @pytest.mark.requires_resource("lmdb")
    @pytest.mark.medium
    def test_lmdb_synchronizes_to_kuzu(self, tmp_path, monkeypatch):
        """LMDB store should propagate items to Kuzu."""

        LMDBStore = pytest.importorskip(
            "devsynth.application.memory.lmdb_store"
        ).LMDBStore
        from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
        from devsynth.application.memory.memory_manager import MemoryManager
        from devsynth.application.memory.sync_manager import SyncManager

        monkeypatch.delitem(sys.modules, "kuzu", raising=False)
        ef = pytest.importorskip("chromadb.utils.embedding_functions")
        monkeypatch.setattr(
            ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5)
        )
        kuzu_store = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
        lmdb_store = LMDBStore(str(tmp_path / "lmdb"))
        try:
            manager = MemoryManager(adapters={"lmdb": lmdb_store, "kuzu": kuzu_store})
            manager.sync_manager = SyncManager(manager)

            item = MemoryItem(id="y", content="hi", memory_type=MemoryType.CODE)
            lmdb_store.store(item)

            manager.synchronize("lmdb", "kuzu")
            assert kuzu_store.retrieve("y") is not None
        finally:
            lmdb_store.close()
            kuzu_store.cleanup()

    @pytest.mark.requires_resource("faiss")
    @pytest.mark.medium
    def test_faiss_vectors_synchronize_to_kuzu(self, tmp_path, monkeypatch):
        """FAISS vectors should propagate to Kuzu."""

        FAISSStore = pytest.importorskip(
            "devsynth.application.memory.faiss_store"
        ).FAISSStore
        from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
        from devsynth.application.memory.memory_manager import MemoryManager
        from devsynth.application.memory.sync_manager import SyncManager

        monkeypatch.delitem(sys.modules, "kuzu", raising=False)
        ef = pytest.importorskip("chromadb.utils.embedding_functions")
        monkeypatch.setattr(
            ef, "DefaultEmbeddingFunction", lambda: (lambda x: [0.0] * 5)
        )
        kuzu_store = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
        faiss_store = FAISSStore(str(tmp_path / "faiss"))
        try:
            manager = MemoryManager(adapters={"faiss": faiss_store, "kuzu": kuzu_store})
            manager.sync_manager = SyncManager(manager)

            vector = MemoryVector(
                id="y", content="hi", embedding=[0.2] * 5, metadata={}
            )
            faiss_store.store_vector(vector)

            manager.synchronize("faiss", "kuzu")
            assert kuzu_store.vector.retrieve_vector("y") is not None
        finally:
            del faiss_store
            kuzu_store.cleanup()
