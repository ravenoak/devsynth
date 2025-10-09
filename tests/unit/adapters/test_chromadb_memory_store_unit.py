"""Unit tests for the ChromaDB memory store without external dependencies."""

from __future__ import annotations

import importlib
import sys
import types
import uuid
from typing import Any, Dict, Iterable, List

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType


class _FakeCollection:
    """Lightweight in-memory collection used by the tests."""

    def __init__(self) -> None:
        self.records: Dict[str, Dict[str, Any]] = {}

    def add(
        self,
        documents: Iterable[str],
        metadatas: Iterable[Dict[str, Any]],
        ids: Iterable[str],
        embeddings: Iterable[List[float]],
    ) -> None:
        for doc, meta, item_id, embedding in zip(documents, metadatas, ids, embeddings):
            self.records[item_id] = {
                "document": doc,
                "metadata": meta,
                "embedding": embedding,
            }

    def get(
        self, ids: Iterable[str] | None = None, include: Iterable[str] | None = None
    ) -> Dict[str, Any]:
        if ids:
            docs: List[str] = []
            metas: List[Dict[str, Any]] = []
            found_ids: List[str] = []
            for item_id in ids:
                record = self.records.get(item_id)
                if record is not None:
                    docs.append(record["document"])
                    metas.append(record["metadata"])
                    found_ids.append(item_id)
            if not docs:
                return {"documents": [], "metadatas": [], "ids": []}
            return {"documents": docs, "metadatas": metas, "ids": found_ids}

        docs = [record["document"] for record in self.records.values()]
        metas = [record["metadata"] for record in self.records.values()]
        ids_list = list(self.records.keys())
        return {"documents": docs, "metadatas": metas, "ids": ids_list}

    def query(
        self, query_embeddings: Iterable[List[float]], n_results: int
    ) -> Dict[str, Any]:
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []
        ids: List[str] = []
        for item_id, record in list(self.records.items())[:n_results]:
            docs.append(record["document"])
            metas.append(record["metadata"])
            ids.append(item_id)
        return {"documents": [docs], "metadatas": [metas], "ids": [ids]}

    def delete(self, ids: Iterable[str]) -> None:
        for item_id in ids:
            self.records.pop(item_id, None)


class _FakeClientAPI:
    """Minimal ChromaDB client for exercising the adapter logic."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.collections: Dict[str, _FakeCollection] = {}
        self.closed = False

    def get_or_create_collection(self, name: str) -> _FakeCollection:
        return self.collections.setdefault(name, _FakeCollection())

    def close(self) -> None:
        self.closed = True


class _FakeSettings:
    """Replacement for chromadb.config.Settings."""

    def __init__(self, persist_directory: str, anonymized_telemetry: bool) -> None:
        self.persist_directory = persist_directory
        self.anonymized_telemetry = anonymized_telemetry


class _FakeEmbeddingFunction:
    """Simple deterministic embedding function used by fallbacks."""

    def __call__(self, text: Any) -> List[float] | List[List[float]]:
        if isinstance(text, str):
            return [0.1, 0.2, 0.3]
        return [[0.1, 0.2, 0.3] for _ in text]


@pytest.fixture
def chromadb_store_factory(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> tuple[Any, Any]:
    """Provide a factory for ChromaDBMemoryStore backed by fake dependencies."""

    fake_main = types.ModuleType("chromadb")
    fake_api = types.ModuleType("chromadb.api")
    fake_config = types.ModuleType("chromadb.config")
    fake_utils = types.ModuleType("chromadb.utils")
    fake_embeddings = types.ModuleType("chromadb.utils.embedding_functions")

    fake_api.ClientAPI = _FakeClientAPI
    fake_config.Settings = _FakeSettings
    fake_embeddings.DefaultEmbeddingFunction = lambda: _FakeEmbeddingFunction()
    fake_utils.embedding_functions = fake_embeddings
    fake_main.api = fake_api
    fake_main.config = fake_config
    fake_main.utils = fake_utils
    fake_main.Client = _FakeClientAPI

    for name, module in {
        "chromadb": fake_main,
        "chromadb.api": fake_api,
        "chromadb.config": fake_config,
        "chromadb.utils": fake_utils,
        "chromadb.utils.embedding_functions": fake_embeddings,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)

    module = importlib.import_module("devsynth.adapters.chromadb_memory_store")
    module = importlib.reload(module)
    module._chromadb_clients.clear()

    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    def factory(**kwargs: Any):
        params = {
            "persist_directory": str(tmp_path),
            "use_provider_system": kwargs.pop("use_provider_system", False),
            "max_retries": kwargs.pop("max_retries", 3),
            "retry_delay": kwargs.pop("retry_delay", 0),
        }
        params.update(kwargs)
        return module.ChromaDBMemoryStore(**params)

    return module, factory


@pytest.mark.fast
def test_transaction_commit_and_delete(chromadb_store_factory) -> None:
    """Ensure staged operations flush during commit and delete. ReqID: CHROMADB-UNIT-1"""

    module, factory = chromadb_store_factory
    store = factory()
    try:
        item = MemoryItem(
            id=str(uuid.uuid4()),
            content="stored item",
            memory_type=MemoryType.WORKING,
            metadata={"note": "unit"},
        )

        tx = store.begin_transaction()
        store.store(item, transaction_id=tx)
        assert item.id not in store.collection.records

        assert store.commit_transaction(tx) is True
        retrieved = store.retrieve(item.id)
        assert retrieved.content == "stored item"

        tx_delete = store.begin_transaction()
        store.delete(item.id, transaction_id=tx_delete)
        assert store.commit_transaction(tx_delete) is True
        with pytest.raises(RuntimeError):
            store.retrieve(item.id)
    finally:
        store.close()


@pytest.mark.fast
def test_provider_fallback_uses_default_embedder(
    chromadb_store_factory, monkeypatch
) -> None:
    """Fallback to the default embedder when provider results are empty. ReqID: CHROMADB-UNIT-2"""

    module, factory = chromadb_store_factory
    store = factory(use_provider_system=True)
    try:
        calls = {"count": 0}

        def failing_embed(*_args, **_kwargs):
            calls["count"] += 1
            return []

        monkeypatch.setattr(module, "embed", failing_embed)

        embedding = store._get_embedding("fallback please")
        assert embedding == [0.1, 0.2, 0.3]
        assert calls["count"] == 1
    finally:
        store.close()


@pytest.mark.fast
def test_store_raises_after_retries(
    monkeypatch: pytest.MonkeyPatch, chromadb_store_factory
) -> None:
    """store surfaces RuntimeError after exhausting retries. ReqID: CHROMADB-UNIT-3"""

    module, factory = chromadb_store_factory
    store = factory(max_retries=2)
    try:
        attempts = {"count": 0}

        def raising_add(*_args, **_kwargs):
            attempts["count"] += 1
            raise RuntimeError("boom")

        monkeypatch.setattr(store.collection, "add", raising_add)
        item = MemoryItem(
            id="retry-item",
            content="retry",
            memory_type=MemoryType.LONG_TERM,
        )
        with pytest.raises(RuntimeError):
            store.store(item)
        assert attempts["count"] == 2
    finally:
        store.close()


@pytest.mark.fast
def test_search_handles_empty_results(chromadb_store_factory) -> None:
    """search returns an empty list when the collection has no matches. ReqID: CHROMADB-UNIT-4"""

    _module, factory = chromadb_store_factory
    store = factory()
    try:
        results = store.search({"query": "no documents", "top_k": 3})
        assert results == []
    finally:
        store.close()


@pytest.mark.fast
def test_commit_failure_marks_transaction(chromadb_store_factory, monkeypatch) -> None:
    """commit_transaction records failures and clears staged operations. ReqID: CHROMADB-UNIT-5"""

    module, factory = chromadb_store_factory
    store = factory()
    try:
        item = MemoryItem(
            id="txn-failure",
            content="txn failure",
            memory_type=MemoryType.WORKING,
        )
        tx = store.begin_transaction()
        store.store(item, transaction_id=tx)

        def raising_add(*_args, **_kwargs):
            raise RuntimeError("cannot persist")

        monkeypatch.setattr(store.collection, "add", raising_add)
        assert store.commit_transaction(tx) is False
        assert store._active_transactions[tx]["status"] == "failed"
        assert tx not in store._transaction_operations
    finally:
        store.close()


@pytest.mark.fast
def test_rollback_transaction_states(chromadb_store_factory) -> None:
    """rollback_transaction handles missing and active transactions. ReqID: CHROMADB-UNIT-6"""

    _module, factory = chromadb_store_factory
    store = factory()
    try:
        assert store.rollback_transaction("missing-tx") is False
        tx = store.begin_transaction()
        assert store.rollback_transaction(tx) is True
        assert store._active_transactions[tx]["status"] == "rolled_back"
    finally:
        store.close()
