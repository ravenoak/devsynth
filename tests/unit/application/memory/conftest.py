"""Shared fixtures for memory adapter unit tests with typed DTOs."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import uuid
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol, TYPE_CHECKING, Callable

import numpy as np

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from devsynth.application.memory.dto import (
        GroupedMemoryResults,
        MemoryMetadata,
        MemoryQueryResults,
        MemoryRecord,
        build_memory_record,
    )
else:
    _SRC_ROOT = Path(__file__).resolve().parents[4] / "src"
    _DTO_SPEC = importlib.util.spec_from_file_location(
        "tests.unit.application.memory._memory_dto",
        _SRC_ROOT / "devsynth" / "application" / "memory" / "dto.py",
    )
    if _DTO_SPEC is None or _DTO_SPEC.loader is None:  # pragma: no cover - defensive
        raise ImportError("Unable to load memory DTO module for fixtures")
    _DTO_MODULE = importlib.util.module_from_spec(_DTO_SPEC)
    sys.modules[_DTO_SPEC.name] = _DTO_MODULE
    _DTO_SPEC.loader.exec_module(_DTO_MODULE)

    GroupedMemoryResults = _DTO_MODULE.GroupedMemoryResults
    MemoryMetadata = _DTO_MODULE.MemoryMetadata
    MemoryQueryResults = _DTO_MODULE.MemoryQueryResults
    MemoryRecord = _DTO_MODULE.MemoryRecord
    build_memory_record = _DTO_MODULE.build_memory_record


def _install_stub(module_name: str, factory: Callable[[], ModuleType]) -> None:
    """Install a stub module if the optional dependency is missing."""

    if module_name in sys.modules:
        return
    sys.modules[module_name] = factory()


def _build_tiktoken_stub() -> ModuleType:
    module = ModuleType("tiktoken")

    class _Encoding:
        def encode(self, text: str) -> list[int]:
            # Keep deterministic length that roughly tracks content size.
            length = max(1, len(text) // 4)
            return list(range(length))

    def get_encoding(name: str) -> _Encoding:  # pragma: no cover - exercised via store
        return _Encoding()

    module.get_encoding = get_encoding  # type: ignore[attr-defined]
    return module


def _build_chromadb_stub() -> ModuleType:
    module = ModuleType("chromadb")

    class _Collection:
        def __init__(self, name: str) -> None:
            self.name = name
            self._items: dict[str, dict[str, Any]] = {}

        def upsert(
            self,
            *,
            ids: list[str],
            documents: list[str],
            metadatas: list[dict[str, Any]],
            embeddings: list[list[float]] | None = None,
        ) -> None:
            for index, (doc, metadata) in enumerate(zip(documents, metadatas)):
                item_id = ids[index]
                payload = {
                    "ids": item_id,
                    "documents": doc,
                    "metadatas": metadata,
                }
                if embeddings is not None:
                    payload["embeddings"] = embeddings[index]
                self._items[item_id] = payload

        def get(
            self,
            ids: list[str] | None = None,
            where: dict[str, Any] | None = None,
        ) -> dict[str, list[Any]]:
            records = list(self._items.values())
            if ids is not None:
                records = [self._items[i] for i in ids if i in self._items]
            if where:
                filtered: list[dict[str, Any]] = []
                for record in records:
                    meta = record.get("metadatas", {})
                    if all(meta.get(key) == value for key, value in where.items()):
                        filtered.append(record)
                records = filtered
            return {
                "ids": [[record["ids"] for record in records]],
                "documents": [[record["documents"] for record in records]],
                "metadatas": [[record.get("metadatas", {}) for record in records]],
            }

        def delete(
            self,
            *,
            ids: list[str] | None = None,
            where: dict[str, Any] | None = None,
        ) -> None:
            if ids is not None:
                for idx in ids:
                    self._items.pop(idx, None)
            elif where:
                to_remove = [
                    key
                    for key, record in self._items.items()
                    if all(record.get("metadatas", {}).get(k) == v for k, v in where.items())
                ]
                for key in to_remove:
                    self._items.pop(key, None)

        def query(
            self,
            *,
            query_texts: list[str],
            where: dict[str, Any] | None = None,
            n_results: int = 5,
            where_document: dict[str, Any] | None = None,
        ) -> dict[str, list[list[Any]]]:
            _ = where_document  # Unused but kept for signature compatibility.
            results = self.get(where=where or {})
            ids = results["ids"][0][:n_results]
            documents = results["documents"][0][:n_results]
            metadatas = results["metadatas"][0][:n_results]
            return {
                "ids": [ids for _ in query_texts],
                "documents": [documents for _ in query_texts],
                "metadatas": [metadatas for _ in query_texts],
            }

    class _Client:
        def __init__(self) -> None:
            self._collections: dict[str, _Collection] = {}

        def get_collection(self, name: str) -> _Collection:
            if name not in self._collections:
                raise RuntimeError("collection not found")
            return self._collections[name]

        def create_collection(self, name: str) -> _Collection:
            coll = _Collection(name)
            self._collections[name] = coll
            return coll

    class PersistentClient(_Client):
        def __init__(self, path: str | None = None) -> None:
            super().__init__()
            self.path = path

    class EphemeralClient(_Client):
        pass

    class HttpClient(_Client):
        def __init__(self, host: str | None = None, port: int | None = None) -> None:
            super().__init__()
            self.host = host
            self.port = port

    module.PersistentClient = PersistentClient  # type: ignore[attr-defined]
    module.EphemeralClient = EphemeralClient  # type: ignore[attr-defined]
    module.HttpClient = HttpClient  # type: ignore[attr-defined]
    utils_module = ModuleType("chromadb.utils")
    embedding_module = ModuleType("chromadb.utils.embedding_functions")

    class _DefaultEmbeddingFunction:
        def __call__(self, _: str) -> list[float]:
            return [0.0] * 5

    def _embedding_factory() -> _DefaultEmbeddingFunction:
        return _DefaultEmbeddingFunction()

    embedding_module.DefaultEmbeddingFunction = _embedding_factory  # type: ignore[attr-defined]
    utils_module.embedding_functions = embedding_module  # type: ignore[attr-defined]
    module.utils = utils_module  # type: ignore[attr-defined]
    sys.modules.setdefault("chromadb.utils", utils_module)
    sys.modules.setdefault("chromadb.utils.embedding_functions", embedding_module)
    return module


class _DuckDBCursor:
    def __init__(self, results: list[tuple[Any, ...]]) -> None:
        self._results = results

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._results[0] if self._results else None

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._results)


_DUCKDB_DATA: dict[str, dict[str, dict[str, Any]]] = defaultdict(
    lambda: {"memory_items": {}, "memory_vectors": {}}
)


def _build_duckdb_stub() -> ModuleType:
    module = ModuleType("duckdb")

    class _Connection:
        def __init__(self, path: str) -> None:
            self._path = path
            self._data = _DUCKDB_DATA[path]

        def execute(self, sql: str, params: Sequence[Any] | None = None) -> _DuckDBCursor:
            statement = " ".join(sql.strip().split())
            params = list(params or [])
            results: list[tuple[Any, ...]] = []

            if statement.startswith("INSTALL vector"):
                return _DuckDBCursor(results)
            if statement.startswith("LOAD vector"):
                return _DuckDBCursor(results)
            if statement.startswith("CREATE TABLE"):
                return _DuckDBCursor(results)
            if statement.startswith("INSERT OR REPLACE INTO memory_items"):
                item_id, content, memory_type, metadata_json, created_at = params
                self._data["memory_items"][item_id] = {
                    "id": item_id,
                    "content": content,
                    "memory_type": memory_type,
                    "metadata": metadata_json,
                    "created_at": created_at,
                }
                return _DuckDBCursor(results)
            if statement.startswith("SELECT id, content, memory_type, metadata, created_at FROM memory_items WHERE id = ?"):
                item_id = params[0]
                item = self._data["memory_items"].get(item_id)
                if item:
                    results = [
                        (
                            item["id"],
                            item["content"],
                            item["memory_type"],
                            item["metadata"],
                            item["created_at"],
                        )
                    ]
                return _DuckDBCursor(results)
            if statement.startswith("SELECT id FROM memory_items WHERE id = ?"):
                item_id = params[0]
                if item_id in self._data["memory_items"]:
                    results = [(item_id,)]
                return _DuckDBCursor(results)
            if statement.startswith("DELETE FROM memory_items WHERE id = ?"):
                item_id = params[0]
                self._data["memory_items"].pop(item_id, None)
                return _DuckDBCursor(results)
            if statement.startswith(
                "SELECT id, content, memory_type, metadata, created_at FROM memory_items WHERE 1=1"
            ):
                records = list(self._data["memory_items"].values())
                idx = 0
                if "memory_type = ?" in statement:
                    match_type = params[idx]
                    idx += 1
                    records = [r for r in records if r["memory_type"] == match_type]
                if "content LIKE ?" in statement:
                    needle = params[idx].strip("%")
                    idx += 1
                    records = [r for r in records if needle in (r["content"] or "")]
                for metadata_match in re.finditer(r"json_extract\(metadata, '\$\.(?P<field>[^']+)'\) = \?", statement):
                    field = metadata_match.group("field")
                    raw = params[idx]
                    idx += 1
                    expected = json.loads(raw) if isinstance(raw, str) and raw.startswith("\"") else raw
                    filtered: list[dict[str, Any]] = []
                    for item in records:
                        metadata = json.loads(item["metadata"]) if item["metadata"] else {}
                        if metadata.get(field) == expected:
                            filtered.append(item)
                    records = filtered
                results = [
                    (
                        item["id"],
                        item["content"],
                        item["memory_type"],
                        item["metadata"],
                        item["created_at"],
                    )
                    for item in records
                ]
                return _DuckDBCursor(results)
            if statement.startswith("INSERT OR REPLACE INTO memory_vectors"):
                vector_id, content, embedding, metadata_json, created_at = params
                stored_embedding = embedding
                if isinstance(embedding, list):
                    stored_embedding = json.dumps(embedding)
                self._data["memory_vectors"][vector_id] = {
                    "id": vector_id,
                    "content": content,
                    "embedding": stored_embedding,
                    "metadata": metadata_json,
                    "created_at": created_at,
                }
                return _DuckDBCursor(results)
            if statement.startswith(
                "SELECT id, content, embedding, metadata, created_at FROM memory_vectors WHERE id = ?"
            ):
                vector_id = params[0]
                vector = self._data["memory_vectors"].get(vector_id)
                if vector:
                    embedding = vector["embedding"]
                    if isinstance(embedding, str):
                        embedding = json.loads(embedding)
                    results = [
                        (
                            vector["id"],
                            vector["content"],
                            embedding,
                            vector["metadata"],
                            vector["created_at"],
                        )
                    ]
                return _DuckDBCursor(results)
            if statement.startswith(
                "SELECT id, content, embedding, metadata, created_at FROM memory_vectors"
            ):
                results = []
                for vector in self._data["memory_vectors"].values():
                    embedding = vector["embedding"]
                    if isinstance(embedding, str):
                        embedding = json.loads(embedding)
                    results.append(
                        (
                            vector["id"],
                            vector["content"],
                            embedding,
                            vector["metadata"],
                            vector["created_at"],
                        )
                    )
                return _DuckDBCursor(results)
            if statement.startswith("DELETE FROM memory_vectors WHERE id = ?"):
                vector_id = params[0]
                self._data["memory_vectors"].pop(vector_id, None)
                return _DuckDBCursor(results)

            raise NotImplementedError(f"Unhandled DuckDB stub statement: {statement}")

    def connect(path: str) -> _Connection:  # pragma: no cover - executed via store
        return _Connection(path)

    module.connect = connect  # type: ignore[attr-defined]
    return module


def _build_kuzu_stub() -> ModuleType:
    module = ModuleType("kuzu")

    class _Connection:
        def __init__(self, db: "_Database") -> None:
            self._db = db

        def execute(self, sql: str) -> None:  # pragma: no cover - simple passthrough
            return None

    class _Database:
        def __init__(self, path: str) -> None:
            self.path = path

    module.Connection = _Connection  # type: ignore[attr-defined]
    module.Database = _Database  # type: ignore[attr-defined]
    return module


def _build_faiss_stub() -> ModuleType:
    module = ModuleType("faiss")

    class IndexFlatL2:
        def __init__(self, dimension: int) -> None:
            self.dimension = dimension
            self._vectors: list[list[float]] = []

        @property
        def ntotal(self) -> int:
            return len(self._vectors)

        def add(self, vectors: np.ndarray) -> None:
            for row in vectors:
                self._vectors.append([float(x) for x in row])

        def search(self, query: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
            if query.size == 0:
                return np.zeros((1, 0), dtype=np.float32), np.zeros((1, 0), dtype=np.int64)
            query_vec = query[0]
            distances = [
                float(np.linalg.norm(np.array(vec, dtype=np.float32) - query_vec))
                for vec in self._vectors
            ]
            indices = list(range(len(self._vectors)))
            ranked = sorted(zip(distances, indices), key=lambda pair: pair[0])[:top_k]
            if not ranked:
                return (
                    np.zeros((1, 0), dtype=np.float32),
                    np.zeros((1, 0), dtype=np.int64),
                )
            ranked_distances, ranked_indices = zip(*ranked)
            return (
                np.array([ranked_distances], dtype=np.float32),
                np.array([ranked_indices], dtype=np.int64),
            )

    def write_index(index: IndexFlatL2, path: str) -> None:
        payload = {"dimension": index.dimension, "vectors": index._vectors}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def read_index(path: str) -> IndexFlatL2:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        idx = IndexFlatL2(payload["dimension"])
        idx._vectors = [list(map(float, vec)) for vec in payload.get("vectors", [])]
        return idx

    def serialize_index(index: IndexFlatL2) -> bytes:
        payload = json.dumps({"dimension": index.dimension, "vectors": index._vectors})
        return payload.encode("utf-8")

    def deserialize_index(buffer: bytes) -> IndexFlatL2:
        payload = json.loads(buffer.decode("utf-8"))
        idx = IndexFlatL2(payload["dimension"])
        idx._vectors = [list(map(float, vec)) for vec in payload.get("vectors", [])]
        return idx

    module.IndexFlatL2 = IndexFlatL2  # type: ignore[attr-defined]
    module.write_index = write_index  # type: ignore[attr-defined]
    module.read_index = read_index  # type: ignore[attr-defined]
    module.serialize_index = serialize_index  # type: ignore[attr-defined]
    module.deserialize_index = deserialize_index  # type: ignore[attr-defined]
    return module


# Install deterministic stubs for optional dependencies so CRUD tests run in isolation.
_install_stub("tiktoken", _build_tiktoken_stub)
_install_stub("chromadb", _build_chromadb_stub)
_install_stub("duckdb", _build_duckdb_stub)
_install_stub("kuzu", _build_kuzu_stub)
_install_stub("faiss", _build_faiss_stub)


@pytest.fixture(autouse=True)
def _set_memory_resource_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure optional memory backends are treated as available in tests."""

    for resource in ("CHROMADB", "KUZU", "DUCKDB", "FAISS"):
        monkeypatch.setenv(f"DEVSYNTH_RESOURCE_{resource}_AVAILABLE", "1")


@pytest.fixture(autouse=True)
def _reset_duckdb_stub_state() -> None:
    """Isolate DuckDB stub data between tests while preserving per-test flows."""

    _DUCKDB_DATA.clear()
    yield
    _DUCKDB_DATA.clear()

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from devsynth.domain.interfaces.memory import ContextManager, MemoryStore, VectorStore
else:

    class MemoryStore(Protocol):
        def store(self, item: MemoryItem) -> str: ...

        def retrieve(self, item_id: str) -> MemoryItem | MemoryRecord | None: ...

        def search(self, query: dict[str, Any] | MemoryMetadata) -> list[MemoryRecord]: ...

        def delete(self, item_id: str) -> bool: ...

        def begin_transaction(self) -> str: ...

        def commit_transaction(self, transaction_id: str) -> bool: ...

        def rollback_transaction(self, transaction_id: str) -> bool: ...

        def is_transaction_active(self, transaction_id: str) -> bool: ...

    class VectorStore(Protocol):
        def store_vector(self, vector: MemoryVector) -> str: ...

        def retrieve_vector(self, vector_id: str) -> MemoryVector | MemoryRecord | None: ...

        def similarity_search(
            self, query_embedding: Sequence[float], top_k: int = 5
        ) -> list[MemoryRecord]: ...

        def delete_vector(self, vector_id: str) -> bool: ...

        def get_collection_stats(self) -> dict[str, Any]: ...

    class ContextManager(Protocol):
        def add_to_context(self, key: str, value: Any) -> None: ...

        def get_from_context(self, key: str) -> Any | None: ...

        def get_full_context(self) -> dict[str, Any]: ...

        def clear_context(self) -> None: ...


class ProtocolCompliantMemoryStore(MemoryStore):
    """In-memory ``MemoryStore`` implementation satisfying the protocol."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._active_transactions: set[str] = set()

    def store(self, item: MemoryItem) -> str:
        if not item.id:
            item.id = str(uuid.uuid4())
        record = build_memory_record(item)
        self._records[item.id] = record
        return item.id

    def retrieve(self, item_id: str) -> MemoryRecord | None:
        return self._records.get(item_id)

    def search(self, query: dict[str, Any] | MemoryMetadata) -> list[MemoryRecord]:
        return list(self._records.values())

    def delete(self, item_id: str) -> bool:
        return self._records.pop(item_id, None) is not None

    def begin_transaction(self) -> str:
        tx_id = f"tx-{len(self._active_transactions) + 1}"
        self._active_transactions.add(tx_id)
        return tx_id

    def commit_transaction(self, transaction_id: str) -> bool:
        if transaction_id in self._active_transactions:
            self._active_transactions.remove(transaction_id)
            return True
        return False

    def rollback_transaction(self, transaction_id: str) -> bool:
        if transaction_id in self._active_transactions:
            self._active_transactions.remove(transaction_id)
            return True
        return False

    def is_transaction_active(self, transaction_id: str) -> bool:
        return transaction_id in self._active_transactions


class ProtocolCompliantVectorStore(VectorStore):
    """Simple ``VectorStore`` implementation for protocol validation."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._vectors: dict[str, MemoryVector] = {}
        self._records: dict[str, MemoryRecord] = {}

    def store_vector(self, vector: MemoryVector) -> str:
        if not vector.id:
            vector.id = str(uuid.uuid4())
        self._vectors[vector.id] = vector
        self._records[vector.id] = build_memory_record(vector, source="vector-fixture")
        return vector.id

    def retrieve_vector(self, vector_id: str) -> MemoryVector | MemoryRecord | None:
        record = self._records.get(vector_id)
        if record is not None:
            return record
        return self._vectors.get(vector_id)

    def similarity_search(
        self, query_embedding: Sequence[float], top_k: int = 5
    ) -> list[MemoryRecord]:
        return list(self._records.values())[:top_k]

    def delete_vector(self, vector_id: str) -> bool:
        removed = False
        if vector_id in self._records:
            del self._records[vector_id]
            removed = True
        if vector_id in self._vectors:
            del self._vectors[vector_id]
            removed = True
        return removed

    def get_collection_stats(self) -> dict[str, int]:
        embedding_dimensions = 0
        if self._vectors:
            first = next(iter(self._vectors.values()))
            embedding_dimensions = len(first.embedding)
        return {
            "vector_count": len(self._vectors),
            "embedding_dimensions": embedding_dimensions,
        }


class ProtocolCompliantContextManager(ContextManager):
    """Minimal context manager satisfying :class:`ContextManager`."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._context: dict[str, Any] = {}

    def add_to_context(self, key: str, value: Any) -> None:
        self._context[key] = value

    def get_from_context(self, key: str) -> Any | None:
        return self._context.get(key)

    def get_full_context(self) -> dict[str, Any]:
        return dict(self._context)

    def clear_context(self) -> None:
        self._context.clear()


__all__ = [
    "ProtocolCompliantContextManager",
    "ProtocolCompliantMemoryStore",
    "ProtocolCompliantVectorStore",
]


@pytest.fixture
def memory_item() -> MemoryItem:
    """Return a representative ``MemoryItem`` instance."""

    return MemoryItem(
        id=str(uuid.uuid4()),
        content="fixture-content",
        memory_type=MemoryType.CONTEXT,
        metadata={"source": "fixture", "iteration": 1},
    )


@pytest.fixture
def memory_vector() -> MemoryVector:
    """Return a representative ``MemoryVector`` instance."""

    return MemoryVector(
        id=str(uuid.uuid4()),
        content="vector-content",
        embedding=[0.1, 0.2, 0.3],
        metadata={"origin": "fixture"},
    )


@pytest.fixture
def memory_record(memory_item: MemoryItem) -> MemoryRecord:
    """Normalize the fixture item into a ``MemoryRecord``."""

    record = build_memory_record(
        memory_item,
        source="fixture-store",
        similarity=0.75,
        metadata={"confidence": 0.9},
    )
    assert isinstance(record.metadata, dict)
    return record


@pytest.fixture
def memory_query_results(memory_record: MemoryRecord) -> MemoryQueryResults:
    """Return a ``MemoryQueryResults`` mapping with the sample record."""

    return {
        "store": "fixture-store",
        "records": [memory_record],
        "total": 1,
        "latency_ms": 1.5,
        "metadata": {"paginated": False},
    }


@pytest.fixture
def grouped_memory_results(
    memory_query_results: MemoryQueryResults,
) -> GroupedMemoryResults:
    """Return grouped results keyed by store name."""

    return {
        "by_store": {memory_query_results["store"]: memory_query_results},
        "combined": list(memory_query_results["records"]),
        "query": "fixture-query",
        "metadata": {"normalized": True},
    }


@pytest.fixture
def protocol_memory_store(memory_record: MemoryRecord) -> ProtocolCompliantMemoryStore:
    """Instantiate a protocol-compliant memory store populated with a record."""

    store = ProtocolCompliantMemoryStore()
    store.store(memory_record.item)
    return store


@pytest.fixture
def protocol_vector_store(memory_vector: MemoryVector) -> ProtocolCompliantVectorStore:
    """Instantiate a protocol-compliant vector store populated with a vector."""

    store = ProtocolCompliantVectorStore()
    store.store_vector(memory_vector)
    return store


@pytest.fixture
def protocol_context_manager() -> ProtocolCompliantContextManager:
    """Return a context manager satisfying the interface."""

    return ProtocolCompliantContextManager()
