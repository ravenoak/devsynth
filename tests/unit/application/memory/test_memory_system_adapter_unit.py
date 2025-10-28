"""Hermetic unit tests for MemorySystemAdapter using lightweight doubles."""

from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from devsynth.adapters.memory.memory_adapter import MemoryStoreError

from .conftest import (
    ProtocolCompliantContextManager,
    ProtocolCompliantMemoryStore,
    ProtocolCompliantVectorStore,
)


@dataclass
class _DummySettings:
    memory_store_type: str
    memory_file_path: str
    max_context_size: int
    context_expiration_days: int
    vector_store_enabled: bool
    provider_type: str | None
    chromadb_collection_name: str
    chromadb_host: str
    chromadb_port: int
    enable_chromadb: bool
    encryption_at_rest: bool
    encryption_key: str | None


@pytest.fixture
def memory_adapter_module(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Reload the adapter with deterministic settings and path utilities."""

    module = importlib.import_module("devsynth.adapters.memory.memory_adapter")
    assert module is sys.modules["devsynth.adapters.memory.memory_adapter"]

    settings = _DummySettings(
        memory_store_type="memory",
        memory_file_path=str(tmp_path / "memory.json"),
        max_context_size=32,
        context_expiration_days=1,
        vector_store_enabled=False,
        provider_type=None,
        chromadb_collection_name="unit-tests",
        chromadb_host="localhost",
        chromadb_port=8000,
        enable_chromadb=False,
        encryption_at_rest=False,
        encryption_key=None,
    )

    monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        module, "ensure_path_exists", lambda path, create=True: str(path)
    )

    return module, settings


@pytest.mark.fast
def test_chromadb_disabled_falls_back_to_memory(memory_adapter_module) -> None:
    """Disabled ChromaDB uses in-memory components. ReqID: MEM-ADAPTER-1"""

    module, settings = memory_adapter_module
    settings.memory_store_type = "chromadb"
    settings.enable_chromadb = False

    adapter = module.MemorySystemAdapter(
        config={"memory_store_type": "chromadb", "enable_chromadb": False},
        create_paths=False,
    )

    assert isinstance(adapter.memory_store, module.InMemoryStore)
    assert isinstance(adapter.get_context_manager(), module.SimpleContextManager)
    assert adapter.get_vector_store() is None


@pytest.mark.fast
def test_chromadb_enabled_uses_adapter_and_store(
    memory_adapter_module, monkeypatch
) -> None:
    """ChromaDB configuration wires vector store and persistence. ReqID: MEM-ADAPTER-2"""

    module, settings = memory_adapter_module
    settings.memory_store_type = "chromadb"
    settings.enable_chromadb = True
    settings.vector_store_enabled = True

    store_instances: list[dict[str, Any]] = []
    adapter_instances: list[dict[str, Any]] = []

    store_module = types.ModuleType("devsynth.application.memory.chromadb_store")

    class _StubChromaDBStore:  # pragma: no cover - exercised via adapter
        def __init__(
            self, persist_directory: str, host: str, port: int, collection_name: str
        ):
            store_instances.append(
                {
                    "persist_directory": persist_directory,
                    "host": host,
                    "port": port,
                    "collection_name": collection_name,
                }
            )
            self.persist_directory = persist_directory

    store_module.ChromaDBStore = _StubChromaDBStore

    adapter_module = types.ModuleType("devsynth.adapters.memory.chroma_db_adapter")

    class _StubChromaDBAdapter:
        def __init__(
            self, persist_directory: str, collection_name: str, host: str, port: int
        ) -> None:
            adapter_instances.append(
                {
                    "persist_directory": persist_directory,
                    "collection_name": collection_name,
                    "host": host,
                    "port": port,
                }
            )

    adapter_module.ChromaDBAdapter = _StubChromaDBAdapter

    monkeypatch.setitem(
        sys.modules, "devsynth.application.memory.chromadb_store", store_module
    )
    monkeypatch.setitem(
        sys.modules, "devsynth.adapters.memory.chroma_db_adapter", adapter_module
    )

    config = {
        "memory_store_type": "chromadb",
        "enable_chromadb": True,
        "vector_store_enabled": True,
        "memory_file_path": settings.memory_file_path,
        "chromadb_collection_name": "unit-collection",
        "chromadb_host": "127.0.0.1",
        "chromadb_port": 9012,
    }
    adapter = module.MemorySystemAdapter(config=config, create_paths=False)

    assert isinstance(adapter.memory_store, _StubChromaDBStore)
    assert adapter.vector_store and isinstance(
        adapter.vector_store, _StubChromaDBAdapter
    )
    assert store_instances[0]["collection_name"] == "unit-collection"
    assert adapter_instances[0]["persist_directory"] == settings.memory_file_path


@pytest.mark.fast
def test_initialize_memory_system_various_backends(
    memory_adapter_module, monkeypatch, tmp_path
) -> None:
    """File, document, and vector backends initialize expected components. ReqID: MEM-ADAPTER-5"""

    module, _settings = memory_adapter_module

    class DummyJSONFileStore(ProtocolCompliantMemoryStore):
        def __init__(
            self,
            path: str,
            *,
            encryption_enabled: bool = False,
            encryption_key: str | None = None,
        ) -> None:
            super().__init__()
            self.path = path
            self.encryption_enabled = encryption_enabled
            self.encryption_key = encryption_key

    class DummyPersistentContextManager(ProtocolCompliantContextManager):
        def __init__(
            self, path: str, *, max_context_size: int, expiration_days: int
        ) -> None:
            super().__init__()
            self.path = path
            self.max_context_size = max_context_size
            self.expiration_days = expiration_days

    class DummyInMemoryStore(ProtocolCompliantMemoryStore):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

    class DummySimpleContextManager(ProtocolCompliantContextManager):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

    class DummyTinyDBStore(DummyJSONFileStore):
        pass

    class DummyDuckDBStore(ProtocolCompliantMemoryStore):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    class DummyFAISSStore(ProtocolCompliantVectorStore):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    class DummyRDFLibStore(ProtocolCompliantMemoryStore):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    monkeypatch.setattr(module, "JSONFileStore", DummyJSONFileStore)
    monkeypatch.setattr(
        module, "PersistentContextManager", DummyPersistentContextManager
    )
    monkeypatch.setattr(module, "InMemoryStore", DummyInMemoryStore)
    monkeypatch.setattr(module, "SimpleContextManager", DummySimpleContextManager)
    monkeypatch.setattr(module, "TinyDBStore", DummyTinyDBStore)
    monkeypatch.setattr(module, "DuckDBStore", DummyDuckDBStore)
    monkeypatch.setattr(module, "FAISSStore", DummyFAISSStore)
    monkeypatch.setattr(module, "RDFLibStore", DummyRDFLibStore)

    file_config = {
        "memory_store_type": "file",
        "memory_file_path": str(tmp_path / "file.json"),
        "encryption_at_rest": True,
        "encryption_key": "secret",
    }
    file_adapter = module.MemorySystemAdapter(config=file_config, create_paths=False)
    assert isinstance(file_adapter.memory_store, DummyJSONFileStore)
    assert file_adapter.memory_store.encryption_enabled is True
    assert isinstance(file_adapter.get_context_manager(), DummyPersistentContextManager)

    tinydb_config = {
        "memory_store_type": "tinydb",
        "memory_file_path": str(tmp_path / "tiny.json"),
    }
    tiny_adapter = module.MemorySystemAdapter(config=tinydb_config, create_paths=False)
    assert isinstance(tiny_adapter.memory_store, DummyTinyDBStore)
    assert isinstance(tiny_adapter.get_context_manager(), DummyPersistentContextManager)

    duckdb_config = {
        "memory_store_type": "duckdb",
        "memory_file_path": str(tmp_path / "duck.db"),
        "vector_store_enabled": True,
    }
    duck_adapter = module.MemorySystemAdapter(config=duckdb_config, create_paths=False)
    assert isinstance(duck_adapter.memory_store, DummyDuckDBStore)
    assert duck_adapter.vector_store is duck_adapter.memory_store

    faiss_config = {
        "memory_store_type": "faiss",
        "memory_file_path": str(tmp_path / "faiss"),
        "vector_store_enabled": True,
    }
    faiss_adapter = module.MemorySystemAdapter(config=faiss_config, create_paths=False)
    assert isinstance(faiss_adapter.vector_store, DummyFAISSStore)

    rdflib_config = {
        "memory_store_type": "rdflib",
        "memory_file_path": str(tmp_path / "rdflib"),
        "vector_store_enabled": True,
    }
    rdflib_adapter = module.MemorySystemAdapter(
        config=rdflib_config, create_paths=False
    )
    assert isinstance(rdflib_adapter.memory_store, DummyRDFLibStore)
    assert rdflib_adapter.vector_store is rdflib_adapter.memory_store

    default_adapter = module.MemorySystemAdapter(
        config={"memory_store_type": "unsupported"},
        create_paths=False,
    )
    assert isinstance(default_adapter.memory_store, DummyInMemoryStore)
    assert isinstance(default_adapter.get_context_manager(), DummySimpleContextManager)


@pytest.mark.fast
def test_kuzu_initialization_and_fallback(
    memory_adapter_module, monkeypatch, tmp_path
) -> None:
    """Kuzu initializes normally and falls back to ChromaDB when flagged. ReqID: MEM-ADAPTER-6"""

    module, settings = memory_adapter_module

    class DummyPersistentContextManager(ProtocolCompliantContextManager):
        def __init__(
            self, path: str, *, max_context_size: int, expiration_days: int
        ) -> None:
            super().__init__()
            self.path = path

    monkeypatch.setattr(
        module, "PersistentContextManager", DummyPersistentContextManager
    )

    class DummyVectorStore(ProtocolCompliantVectorStore):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

    class DummyKuzuStore(ProtocolCompliantMemoryStore):
        def __init__(self, path: str, *, provider_type: str | None = None) -> None:
            super().__init__()
            self.path = path
            self.provider_type = provider_type
            self.vector = DummyVectorStore()
            self._store = types.SimpleNamespace(_use_fallback=False)

    monkeypatch.setattr(module, "KuzuMemoryStore", DummyKuzuStore)

    normal_config = {
        "memory_store_type": "kuzu",
        "memory_file_path": str(tmp_path / "kuzu.db"),
        "vector_store_enabled": True,
        "provider_type": "azure",
    }
    normal_adapter = module.MemorySystemAdapter(
        config=normal_config, create_paths=False
    )
    assert isinstance(normal_adapter.memory_store, DummyKuzuStore)
    assert normal_adapter.vector_store is normal_adapter.memory_store.vector

    class FallbackKuzuStore(DummyKuzuStore):
        def __init__(self, path: str, *, provider_type: str | None = None) -> None:
            super().__init__(path, provider_type=provider_type)
            self._store = types.SimpleNamespace(_use_fallback=True)

    monkeypatch.setattr(module, "KuzuMemoryStore", FallbackKuzuStore)

    chroma_store_module = types.ModuleType("devsynth.application.memory.chromadb_store")
    chroma_adapter_module = types.ModuleType(
        "devsynth.adapters.memory.chroma_db_adapter"
    )

    class StubChromaDBStore(ProtocolCompliantMemoryStore):
        def __init__(
            self,
            path: str,
            *,
            host: str | None = None,
            port: int | None = None,
            collection_name: str | None = None,
        ) -> None:
            super().__init__()
            self.path = path
            self.host = host
            self.port = port
            self.collection_name = collection_name

    class StubChromaDBAdapter(ProtocolCompliantVectorStore):
        def __init__(
            self,
            *,
            persist_directory: str,
            collection_name: str,
            host: str | None = None,
            port: int | None = None,
        ) -> None:
            super().__init__()
            self.persist_directory = persist_directory
            self.collection_name = collection_name
            self.host = host
            self.port = port

    chroma_store_module.ChromaDBStore = StubChromaDBStore
    chroma_adapter_module.ChromaDBAdapter = StubChromaDBAdapter
    monkeypatch.setitem(
        sys.modules, "devsynth.application.memory.chromadb_store", chroma_store_module
    )
    monkeypatch.setitem(
        sys.modules, "devsynth.adapters.memory.chroma_db_adapter", chroma_adapter_module
    )

    fallback_config = {
        "memory_store_type": "kuzu",
        "memory_file_path": str(tmp_path / "fallback"),
        "vector_store_enabled": True,
        "enable_chromadb": True,
        "chromadb_collection_name": "fallback",
        "chromadb_host": "localhost",
        "chromadb_port": 9010,
    }
    fallback_adapter = module.MemorySystemAdapter(
        config=fallback_config, create_paths=False
    )
    assert isinstance(fallback_adapter.memory_store, StubChromaDBStore)
    assert isinstance(fallback_adapter.vector_store, StubChromaDBAdapter)


@pytest.mark.fast
def test_lmdb_missing_falls_back_to_memory(
    memory_adapter_module, monkeypatch, tmp_path
) -> None:
    """LMDB absence triggers an in-memory fallback. ReqID: MEM-ADAPTER-7"""

    module, _settings = memory_adapter_module

    class DummyInMemoryStore(ProtocolCompliantMemoryStore):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

    class DummySimpleContextManager(ProtocolCompliantContextManager):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

    monkeypatch.setattr(module, "LMDBStore", None)
    monkeypatch.setattr(module, "_LMDB_ERROR", RuntimeError("missing"))
    monkeypatch.setattr(module, "InMemoryStore", DummyInMemoryStore)
    monkeypatch.setattr(module, "SimpleContextManager", DummySimpleContextManager)

    adapter = module.MemorySystemAdapter(
        config={
            "memory_store_type": "lmdb",
            "memory_file_path": str(tmp_path / "lmdb"),
        },
        create_paths=False,
    )
    assert isinstance(adapter.memory_store, DummyInMemoryStore)
    assert isinstance(adapter.get_context_manager(), DummySimpleContextManager)


@pytest.mark.fast
def test_initialize_memory_system_branches_execution(
    memory_adapter_module, monkeypatch, tmp_path
) -> None:
    """Directly exercise initialization branches for broad coverage. ReqID: MEM-ADAPTER-8"""

    module, _settings = memory_adapter_module

    class DummyInMemoryStore(ProtocolCompliantMemoryStore):
        def __init__(self) -> None:
            super().__init__()
            self.vector = types.SimpleNamespace()

    class DummySimpleContextManager(ProtocolCompliantContextManager):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__()

    class DummyJSONFileStore(ProtocolCompliantMemoryStore):
        def __init__(
            self,
            path: str,
            *,
            encryption_enabled: bool = False,
            encryption_key: str | None = None,
        ) -> None:
            super().__init__()
            self.path = path
            self.encryption_enabled = encryption_enabled
            self.encryption_key = encryption_key

    class DummyPersistentContextManager(ProtocolCompliantContextManager):
        def __init__(
            self, path: str, *, max_context_size: int, expiration_days: int
        ) -> None:
            super().__init__()
            self.path = path

    class DummyTinyDBStore(DummyJSONFileStore):
        pass

    class DummyDuckDBStore(ProtocolCompliantMemoryStore):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

        def flush(self) -> None:
            pass

    class DummyFAISSStore(ProtocolCompliantVectorStore):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    class DummyRDFLibStore(ProtocolCompliantMemoryStore):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    class DummyKuzuStore(ProtocolCompliantMemoryStore):
        def __init__(self, path: str, *, provider_type: str | None = None) -> None:
            super().__init__()
            self.path = path
            self.provider_type = provider_type
            self.vector = types.SimpleNamespace()
            self._store = types.SimpleNamespace(_use_fallback=False)

    class FallbackKuzuStore(DummyKuzuStore):
        def __init__(self, path: str, *, provider_type: str | None = None) -> None:
            super().__init__(path, provider_type=provider_type)
            self._store = types.SimpleNamespace(_use_fallback=True)

    monkeypatch.setattr(module, "InMemoryStore", DummyInMemoryStore)
    monkeypatch.setattr(module, "SimpleContextManager", DummySimpleContextManager)
    monkeypatch.setattr(module, "JSONFileStore", DummyJSONFileStore)
    monkeypatch.setattr(
        module, "PersistentContextManager", DummyPersistentContextManager
    )
    monkeypatch.setattr(module, "TinyDBStore", DummyTinyDBStore)
    monkeypatch.setattr(module, "DuckDBStore", DummyDuckDBStore)
    monkeypatch.setattr(module, "FAISSStore", DummyFAISSStore)
    monkeypatch.setattr(module, "RDFLibStore", DummyRDFLibStore)
    monkeypatch.setattr(module, "KuzuMemoryStore", DummyKuzuStore)

    adapter = module.MemorySystemAdapter(
        config={"memory_store_type": "memory"}, create_paths=False
    )

    adapter.storage_type = "file"
    adapter.memory_path = str(tmp_path / "file.json")
    adapter.encryption_at_rest = True
    adapter.encryption_key = "secret"
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyJSONFileStore)

    adapter.storage_type = "chromadb"
    adapter.memory_path = str(tmp_path / "chromadb")
    adapter.enable_chromadb = False
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyInMemoryStore)

    adapter.enable_chromadb = True
    adapter.vector_store_enabled = True
    chroma_store_module = types.ModuleType("devsynth.application.memory.chromadb_store")
    chroma_adapter_module = types.ModuleType(
        "devsynth.adapters.memory.chroma_db_adapter"
    )

    class StubChromaDBStore:
        def __init__(
            self,
            path: str,
            *,
            host: str | None = None,
            port: int | None = None,
            collection_name: str | None = None,
        ) -> None:
            self.path = path
            self.collection_name = collection_name

    class StubChromaDBAdapter:
        def __init__(
            self,
            *,
            persist_directory: str,
            collection_name: str,
            host: str | None = None,
            port: int | None = None,
        ) -> None:
            self.persist_directory = persist_directory
            self.collection_name = collection_name

    chroma_store_module.ChromaDBStore = StubChromaDBStore
    chroma_adapter_module.ChromaDBAdapter = StubChromaDBAdapter
    monkeypatch.setitem(
        sys.modules, "devsynth.application.memory.chromadb_store", chroma_store_module
    )
    monkeypatch.setitem(
        sys.modules, "devsynth.adapters.memory.chroma_db_adapter", chroma_adapter_module
    )

    adapter.chromadb_collection_name = "coverage"
    adapter.chromadb_host = "localhost"
    adapter.chromadb_port = 9999
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, StubChromaDBStore)
    assert isinstance(adapter.vector_store, StubChromaDBAdapter)

    adapter.storage_type = "kuzu"
    adapter.memory_path = str(tmp_path / "kuzu")
    adapter.vector_store_enabled = True
    adapter.enable_chromadb = False
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyKuzuStore)
    assert adapter.vector_store is adapter.memory_store.vector

    monkeypatch.setattr(module, "KuzuMemoryStore", FallbackKuzuStore)
    adapter.enable_chromadb = True
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, StubChromaDBStore)

    adapter.storage_type = "tinydb"
    adapter.memory_path = str(tmp_path / "tiny")
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyTinyDBStore)

    adapter.storage_type = "duckdb"
    adapter.memory_path = str(tmp_path / "duck")
    adapter.vector_store_enabled = True
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyDuckDBStore)
    assert adapter.vector_store is adapter.memory_store

    adapter.storage_type = "lmdb"
    monkeypatch.setattr(module, "LMDBStore", None)
    monkeypatch.setattr(module, "_LMDB_ERROR", RuntimeError("missing"))
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyInMemoryStore)

    monkeypatch.setattr(module, "LMDBStore", DummyTinyDBStore)
    adapter.storage_type = "lmdb"
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyTinyDBStore)

    adapter.storage_type = "faiss"
    adapter.vector_store_enabled = True
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.vector_store, DummyFAISSStore)

    adapter.storage_type = "rdflib"
    adapter.vector_store_enabled = True
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyRDFLibStore)
    assert adapter.vector_store is adapter.memory_store

    adapter.storage_type = "unknown"
    adapter._initialize_memory_system(create_paths=False)
    assert isinstance(adapter.memory_store, DummyInMemoryStore)
    assert isinstance(adapter.context_manager, DummySimpleContextManager)


class _CacheAwareStore:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}
        self.transactions: dict[str, str] = {}
        self.query_history: list[Any] = []
        self.metadata_history: list[Any] = []
        self.search_history: list[Any] = []
        self.flushed = False
        self.token_usage = 7
        self.tx_counter = 0

    def store(self, item: dict[str, Any]) -> str:
        item_id = item["id"]
        self.records[item_id] = item
        return item_id

    def query_by_type(self, memory_type: Any) -> list[Any]:
        self.query_history.append(memory_type)
        return [f"type:{memory_type}"]

    def query_by_metadata(self, metadata: dict[str, Any]) -> list[Any]:
        self.metadata_history.append(metadata)
        return [metadata]

    def search(self, query: dict[str, Any]) -> list[Any]:
        self.search_history.append(query)
        return [query]

    def retrieve(self, item_id: str) -> dict[str, Any] | None:
        return self.records.get(item_id)

    def delete(self, item_id: str) -> bool:
        self.records.pop(item_id, None)
        return True

    def get_all(self) -> list[dict[str, Any]]:
        return list(self.records.values())

    def get_token_usage(self) -> int:
        return self.token_usage

    def begin_transaction(self) -> str:
        self.tx_counter += 1
        tx_id = f"tx-{self.tx_counter}"
        self.transactions[tx_id] = "active"
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        if self.transactions.get(transaction_id) != "active":
            raise RuntimeError("not active")
        self.transactions[transaction_id] = "committed"
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        if transaction_id not in self.transactions:
            raise RuntimeError("unknown")
        self.transactions[transaction_id] = "rolled_back"
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        return self.transactions.get(transaction_id) == "active"

    def flush(self) -> None:
        self.flushed = True


class _FakeTieredCache:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size
        self.items: dict[str, Any] = {}
        self.removed: list[str] = []
        self.cleared = False

    def size(self) -> int:
        return len(self.items)

    def clear(self) -> None:
        self.items.clear()
        self.cleared = True

    def remove(self, item_id: str) -> None:
        self.removed.append(item_id)
        self.items.pop(item_id, None)


@pytest.mark.fast
def test_cache_and_transaction_workflow(memory_adapter_module, monkeypatch) -> None:
    """Exercise cache management, querying, and transaction helpers. ReqID: MEM-ADAPTER-3"""

    module, _settings = memory_adapter_module
    monkeypatch.setattr(module, "TieredCache", _FakeTieredCache)

    store = _CacheAwareStore()
    context = types.SimpleNamespace(get_token_usage=lambda: 3, flush=lambda: None)
    vector = types.SimpleNamespace(flush=lambda: None)

    adapter = module.MemorySystemAdapter(
        config={"memory_store_type": "memory"},
        memory_store=store,
        context_manager=context,
        vector_store=vector,
        create_paths=False,
    )

    adapter.enable_tiered_cache(max_size=5)
    assert adapter.is_tiered_cache_enabled() is True
    assert adapter.get_cache_size() == 0
    assert adapter.get_cache_stats() == {"hits": 0, "misses": 0}

    adapter.cache.items["stale"] = {"id": "stale"}
    stored_id = adapter.store({"id": "item-1"})
    assert stored_id == "item-1"
    assert adapter.cache.removed == ["item-1"]

    adapter.clear_cache()
    assert adapter.cache.cleared is True
    adapter.disable_tiered_cache()
    assert adapter.is_tiered_cache_enabled() is False
    assert adapter.get_cache_size() == 0

    assert adapter.query_by_type("working") == ["type:working"]
    assert adapter.query_by_metadata({"owner": "dev"}) == [{"owner": "dev"}]
    assert adapter.search({"tag": "demo"}) == [{"tag": "demo"}]
    assert adapter.retrieve("item-1") == {"id": "item-1"}
    assert adapter.get_all() == [{"id": "item-1"}]
    assert adapter.get_token_usage() == {
        "memory_tokens": 7,
        "context_tokens": 3,
        "total_tokens": 10,
    }

    adapter.flush()
    assert store.flushed is True

    tx = adapter.begin_transaction()
    assert store.is_transaction_active(tx) is True
    assert adapter.commit_transaction(tx) is True
    assert store.is_transaction_active(tx) is False

    tx2 = adapter.begin_transaction()
    assert adapter.rollback_transaction(tx2) is True
    assert store.transactions[tx2] == "rolled_back"

    result = adapter.execute_in_transaction([lambda: adapter.store({"id": "item-2"})])
    assert result == "item-2"
    assert "item-2" in store.records

    fallback_called: list[str] = []

    def failing_operation():
        raise RuntimeError("boom")

    with pytest.raises(MemoryStoreError):
        adapter.execute_in_transaction(
            [failing_operation],
            fallback_operations=[lambda: fallback_called.append("fallback")],
        )
    assert fallback_called == ["fallback"]

    # query_by_type fallback to search
    class _SearchOnlyStore:
        def __init__(self) -> None:
            self.last_query = None

        def search(self, query: dict[str, Any]) -> list[str]:
            self.last_query = query
            return ["search-result"]

    search_store = _SearchOnlyStore()
    adapter.memory_store = search_store
    assert adapter.query_by_type("archival") == ["search-result"]
    assert search_store.last_query == {"memory_type": "archival"}

    # query_by_type with no support
    adapter.memory_store = object()
    assert adapter.query_by_type("none") == []

    # query_by_metadata fallback
    adapter.memory_store = search_store
    assert adapter.query_by_metadata({"scope": "unit"}) == ["search-result"]
    adapter.memory_store = object()
    assert adapter.query_by_metadata({"scope": "unit"}) == []


@pytest.mark.fast
def test_transaction_wrappers_raise_without_support(memory_adapter_module) -> None:
    """Adapters raise MemoryStoreError when underlying store lacks hooks. ReqID: MEM-ADAPTER-4"""

    module, _settings = memory_adapter_module
    adapter = module.MemorySystemAdapter(
        config={"memory_store_type": "memory"},
        memory_store=object(),
        context_manager=types.SimpleNamespace(),
        vector_store=None,
        create_paths=False,
    )

    with pytest.raises(MemoryStoreError):
        adapter.begin_transaction()
    with pytest.raises(MemoryStoreError):
        adapter.commit_transaction("tx")
    with pytest.raises(MemoryStoreError):
        adapter.rollback_transaction("tx")
    with pytest.raises(MemoryStoreError):
        adapter.is_transaction_active("tx")
