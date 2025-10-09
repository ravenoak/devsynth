"""Shared fixtures for memory adapter unit tests with typed DTOs."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import uuid
from collections import defaultdict
from collections.abc import Mapping, MutableMapping, Sequence
from math import sqrt
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

_NUMPY_SPEC = importlib.util.find_spec("numpy")
if _NUMPY_SPEC is not None:  # pragma: no branch - deterministic path selection
    import numpy as np  # type: ignore[import-not-found]
else:
    np = None  # type: ignore[assignment]

import pytest
from typing_extensions import Protocol

from devsynth.application.memory.adapters._chromadb_protocols import (
    ChromaClientProtocol,
    ChromaCollectionProtocol,
    ChromaEmbeddingFunctionProtocol,
    ChromaGetResult,
    ChromaQueryResult,
)
from devsynth.application.memory.adapters._duckdb_protocols import (
    DuckDBConnectionProtocol,
    DuckDBModuleProtocol,
    DuckDBResultProtocol,
)
from devsynth.application.memory.adapters._tinydb_protocols import (
    TinyDBFactory,
    TinyDBLike,
    TinyDBQueryFactory,
    TinyDBQueryLike,
    TinyDBTableLike,
)
from devsynth.application.memory.context_manager import ContextState, ContextValue
from devsynth.application.memory.dto import (
    GroupedMemoryResults,
    MemoryMetadata,
    MemoryQueryResults,
    MemoryRecord,
    MemorySearchQuery,
    VectorStoreStats,
    build_memory_record,
)
from devsynth.application.memory.vector_protocol import EmbeddingVector
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

T_Module = TypeVar("T_Module", bound=ModuleType)


def _install_stub(module_name: str, factory: Callable[[], T_Module]) -> T_Module:
    """Install a stub module if the optional dependency is missing."""

    existing = sys.modules.get(module_name)
    if isinstance(existing, ModuleType):
        return cast(T_Module, existing)

    module = factory()
    sys.modules[module_name] = module
    return module


if np is None:

    def _build_numpy_stub() -> ModuleType:
        module = ModuleType("numpy")

        class _Array(list):
            def __init__(self, values: Sequence[object] | object) -> None:
                normalized = _normalize(values)
                if not isinstance(normalized, list):
                    normalized = [normalized]
                super().__init__(normalized)

            @property
            def shape(self) -> tuple[int, ...]:
                return _shape(self)

            @property
            def size(self) -> int:
                dims = self.shape
                if not dims:
                    return 0
                total = 1
                for dim in dims:
                    total *= dim
                return total

        def _normalize(value: Sequence[object] | object) -> list[object] | object:
            if isinstance(value, _Array):
                return list(value)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                return [_normalize(item) for item in value]
            try:
                return float(value)  # type: ignore[arg-type]
            except Exception:
                return value

        def _shape(value: Sequence[object] | object) -> tuple[int, ...]:
            if isinstance(value, _Array):
                return _shape(list(value))
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                if not value:
                    return (0,)
                inner = _shape(value[0])
                return (len(value),) + inner
            return ()

        def _flatten(value: Sequence[object] | object) -> list[float]:
            if isinstance(value, _Array):
                return _flatten(list(value))
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                items: list[float] = []
                for item in value:
                    items.extend(_flatten(item))
                return items
            try:
                return [float(value)]
            except Exception:
                return [0.0]

        def array(
            values: Sequence[object] | object, dtype: object | None = None
        ) -> _Array:
            return _Array(values)

        def _zeros(shape: Sequence[int] | int) -> list[object]:
            if isinstance(shape, int):
                shape = (shape,)
            shape_tuple = tuple(int(dim) for dim in shape)
            if not shape_tuple:
                return [0.0]
            if len(shape_tuple) == 1:
                return [0.0 for _ in range(max(shape_tuple[0], 0))]
            length = max(shape_tuple[0], 0)
            return [_zeros(shape_tuple[1:]) for _ in range(length)]

        def zeros(shape: Sequence[int] | int, dtype: object | None = None) -> _Array:
            return _Array(_zeros(shape))

        def dot(a: Sequence[object] | object, b: Sequence[object] | object) -> float:
            seq_a = _flatten(a)
            seq_b = _flatten(b)
            return sum(x * y for x, y in zip(seq_a, seq_b))

        def allclose(
            a: Sequence[object] | object,
            b: Sequence[object] | object,
            *,
            atol: float = 1e-8,
        ) -> bool:
            seq_a = _flatten(a)
            seq_b = _flatten(b)
            if len(seq_a) != len(seq_b):
                return False
            return all(abs(x - y) <= atol for x, y in zip(seq_a, seq_b))

        def norm(value: Sequence[object] | object) -> float:
            return sqrt(sum(component * component for component in _flatten(value)))

        module.array = array  # type: ignore[attr-defined]
        module.asarray = array  # type: ignore[attr-defined]
        module.zeros = zeros  # type: ignore[attr-defined]
        module.dot = dot  # type: ignore[attr-defined]
        module.allclose = allclose  # type: ignore[attr-defined]
        module.float32 = float  # type: ignore[attr-defined]
        module.int64 = int  # type: ignore[attr-defined]
        module.ndarray = _Array  # type: ignore[attr-defined]
        module.linalg = SimpleNamespace(norm=norm)  # type: ignore[attr-defined]
        return module

    np = _install_stub("numpy", _build_numpy_stub)


class MemoryRecordFactory(Protocol):
    def __call__(
        self,
        payload: (
            MemoryRecord
            | MemoryItem
            | MemoryVector
            | Mapping[str, object]
            | tuple[
                MemoryRecord | MemoryItem | MemoryVector | Mapping[str, object],
                float | int | None,
            ]
            | None
        ),
        *,
        source: str | None = ...,
        similarity: float | None = ...,
        metadata: MemoryMetadata | None = ...,
    ) -> MemoryRecord: ...


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
    class _ChromaDBModule(ModuleType):
        PersistentClient: type[ChromaClientProtocol]
        EphemeralClient: type[ChromaClientProtocol]
        HttpClient: type[ChromaClientProtocol]
        utils: ModuleType

    module = _ChromaDBModule("chromadb")

    class _Collection:
        def __init__(self, name: str) -> None:
            self.name = name
            self._items: dict[str, dict[str, object]] = {}

        def add(
            self,
            *,
            ids: Sequence[str],
            embeddings: Sequence[Sequence[float]],
            metadatas: Sequence[Mapping[str, object]],
            documents: Sequence[object],
        ) -> None:
            for idx, item_id in enumerate(ids):
                payload: dict[str, object] = {
                    "ids": item_id,
                    "documents": documents[idx],
                    "metadatas": dict(metadatas[idx]),
                }
                embedding = list(embeddings[idx]) if embeddings else []
                payload["embeddings"] = [float(value) for value in embedding]
                self._items[item_id] = payload

        def get(
            self,
            ids: Sequence[str] | None = None,
            include: Sequence[str] | None = None,
        ) -> ChromaGetResult | None:
            records = list(self._items.values())
            if ids is not None:
                records = [
                    self._items[item_id] for item_id in ids if item_id in self._items
                ]
            if not records:
                return None

            result: ChromaGetResult = {
                "ids": [cast(str, record["ids"]) for record in records],
                "documents": [record.get("documents") for record in records],
                "metadatas": [
                    cast(Mapping[str, object], record.get("metadatas", {}))
                    for record in records
                ],
            }
            if include and "embeddings" in include:
                result["embeddings"] = [
                    cast(list[float], record.get("embeddings", []))
                    for record in records
                ]
            return result

        def delete(self, *, ids: Sequence[str]) -> None:
            for identifier in ids:
                self._items.pop(identifier, None)

        def query(
            self,
            *,
            query_embeddings: Sequence[Sequence[float]],
            n_results: int,
            include: Sequence[str],
        ) -> ChromaQueryResult | None:
            _ = query_embeddings
            if not self._items:
                return None

            records = list(self._items.values())[:n_results]
            ids = [cast(str, record["ids"]) for record in records]
            documents = [record.get("documents") for record in records]
            metadatas = [
                cast(Mapping[str, object], record.get("metadatas", {}))
                for record in records
            ]
            embeddings: list[list[float]] = [
                cast(list[float], record.get("embeddings", [])) for record in records
            ]

            result: ChromaQueryResult = {
                "ids": [ids for _ in query_embeddings],
                "documents": (
                    [documents for _ in query_embeddings]
                    if "documents" in include
                    else []
                ),
                "metadatas": (
                    [metadatas for _ in query_embeddings]
                    if "metadatas" in include
                    else []
                ),
                "embeddings": (
                    [embeddings for _ in query_embeddings]
                    if "embeddings" in include
                    else []
                ),
            }
            return result

    class _Client:
        def __init__(self) -> None:
            self._collections: dict[str, _Collection] = {}

        def get_or_create_collection(
            self,
            name: str,
            embedding_function: ChromaEmbeddingFunctionProtocol | None = None,
        ) -> ChromaCollectionProtocol:
            _ = embedding_function
            collection = self._collections.get(name)
            if collection is None:
                collection = _Collection(name)
                self._collections[name] = collection
            return cast(ChromaCollectionProtocol, collection)

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

    module.PersistentClient = PersistentClient
    module.EphemeralClient = EphemeralClient
    module.HttpClient = HttpClient

    class _EmbeddingFunctionsModule(ModuleType):
        DefaultEmbeddingFunction: Callable[[], ChromaEmbeddingFunctionProtocol]

    class _UtilsModule(ModuleType):
        embedding_functions: ModuleType

    utils_module = _UtilsModule("chromadb.utils")
    embedding_module = _EmbeddingFunctionsModule("chromadb.utils.embedding_functions")

    class _DefaultEmbeddingFunction:
        def __call__(self, inputs: Sequence[str]) -> Sequence[Sequence[float]]:
            return [[0.0] * 5 for _ in inputs]

    def _embedding_factory() -> ChromaEmbeddingFunctionProtocol:
        return cast(ChromaEmbeddingFunctionProtocol, _DefaultEmbeddingFunction())

    embedding_module.DefaultEmbeddingFunction = _embedding_factory
    utils_module.embedding_functions = embedding_module
    module.utils = utils_module

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
    class _DuckDBModule(ModuleType):
        def connect(
            self,
            database: str | None = None,
            read_only: bool | None = None,
        ) -> DuckDBConnectionProtocol:
            _ = read_only
            path = database or ":memory:"
            return cast(DuckDBConnectionProtocol, _Connection(path))

    module = _DuckDBModule("duckdb")

    class _Connection:
        def __init__(self, path: str) -> None:
            self._path = path
            self._data = _DUCKDB_DATA[path]
            self._last_cursor: _DuckDBCursor | None = None

        def _cursor(self, results: list[tuple[Any, ...]]) -> _DuckDBCursor:
            cursor = _DuckDBCursor(results)
            self._last_cursor = cursor
            return cursor

        def execute(
            self, sql: str, params: Sequence[Any] | None = None
        ) -> DuckDBResultProtocol:
            statement = " ".join(sql.strip().split())
            params = list(params or [])
            results: list[tuple[Any, ...]] = []

            if statement.startswith("INSTALL vector"):
                return self._cursor(results)
            if statement.startswith("LOAD vector"):
                return self._cursor(results)
            if statement.startswith("CREATE TABLE"):
                return self._cursor(results)
            if statement.startswith("INSERT OR REPLACE INTO memory_items"):
                item_id, content, memory_type, metadata_json, created_at = params
                self._data["memory_items"][item_id] = {
                    "id": item_id,
                    "content": content,
                    "memory_type": memory_type,
                    "metadata": metadata_json,
                    "created_at": created_at,
                }
                return self._cursor(results)
            if statement.startswith(
                "SELECT id, content, memory_type, metadata, created_at FROM memory_items WHERE id = ?"
            ):
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
                return self._cursor(results)
            if statement.startswith("SELECT id FROM memory_items WHERE id = ?"):
                item_id = params[0]
                if item_id in self._data["memory_items"]:
                    results = [(item_id,)]
                return self._cursor(results)
            if statement.startswith("DELETE FROM memory_items WHERE id = ?"):
                item_id = params[0]
                self._data["memory_items"].pop(item_id, None)
                return self._cursor(results)
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
                for metadata_match in re.finditer(
                    r"json_extract\(metadata, '\$\.(?P<field>[^']+)'\) = \?",
                    statement,
                ):
                    field = metadata_match.group("field")
                    raw = params[idx]
                    idx += 1
                    expected = (
                        json.loads(raw)
                        if isinstance(raw, str) and raw.startswith('"')
                        else raw
                    )
                    filtered: list[dict[str, Any]] = []
                    for item in records:
                        metadata = (
                            json.loads(item["metadata"]) if item["metadata"] else {}
                        )
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
                return self._cursor(results)
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
                return self._cursor(results)
            if statement.startswith(
                "SELECT id, content, embedding, metadata, created_at FROM memory_vectors WHERE id = ?"
            ):
                vector_id = params[0]
                vector = self._data["memory_vectors"].get(vector_id)
                if vector:
                    embedding = vector["embedding"]
                    results = [
                        (
                            vector["id"],
                            vector["content"],
                            embedding,
                            vector["metadata"],
                            vector["created_at"],
                        )
                    ]
                return self._cursor(results)
            if statement.startswith(
                "SELECT id, content, embedding, metadata, created_at FROM memory_vectors"
            ):
                results = []
                for vector in self._data["memory_vectors"].values():
                    embedding = vector["embedding"]
                    results.append(
                        (
                            vector["id"],
                            vector["content"],
                            embedding,
                            vector["metadata"],
                            vector["created_at"],
                        )
                    )
                return self._cursor(results)
            if statement.startswith("DELETE FROM memory_vectors WHERE id = ?"):
                vector_id = params[0]
                self._data["memory_vectors"].pop(vector_id, None)
                return self._cursor(results)
            return self._cursor(results)

        def fetchone(self) -> tuple[Any, ...] | None:
            if self._last_cursor is None:
                return None
            return self._last_cursor.fetchone()

        def fetchall(self) -> list[tuple[Any, ...]]:
            if self._last_cursor is None:
                return []
            return self._last_cursor.fetchall()

        def close(self) -> None:
            self._last_cursor = None

    return module


def _build_tinydb_stub() -> ModuleType:
    class _TinyDBModule(ModuleType):
        TinyDB: type[TinyDBLike]
        Query: TinyDBQueryFactory
        storages: ModuleType
        middlewares: ModuleType

    module = _TinyDBModule("tinydb")

    class _TinyDBQuery:
        def __init__(
            self,
            path: tuple[str, ...] = (),
            predicate: Callable[[Mapping[str, Any]], bool] | None = None,
        ) -> None:
            self._path = path
            self._predicate = predicate

        def __getattr__(self, name: str) -> "_TinyDBQuery":
            return _TinyDBQuery(self._path + (name,), self._predicate)

        def __getitem__(self, item: str) -> "_TinyDBQuery":
            return self.__getattr__(item)

        def __and__(self, other: TinyDBQueryLike) -> TinyDBQueryLike:
            def _combined(document: Mapping[str, Any]) -> bool:
                return self(document) and bool(other(document))

            return _TinyDBQuery(predicate=_combined)

        def __call__(self, document: Mapping[str, Any]) -> bool:
            if self._predicate is not None:
                return self._predicate(document)
            current: object = document
            for part in self._path:
                if isinstance(current, Mapping) and part in current:
                    current = current[part]
                else:
                    return False
            return bool(current)

        def __eq__(self, other: object) -> TinyDBQueryLike:  # type: ignore[override]
            path = self._path

            def _predicate(document: Mapping[str, Any]) -> bool:
                current: object = document
                for part in path:
                    if isinstance(current, Mapping) and part in current:
                        current = current[part]
                    else:
                        return False
                return current == other

            return _TinyDBQuery(predicate=_predicate)

    class _TinyDBTable(TinyDBTableLike):
        def __init__(self) -> None:
            self._rows: list[MutableMapping[str, Any]] = []

        def _matches(self, cond: TinyDBQueryLike, row: Mapping[str, Any]) -> bool:
            try:
                return bool(cond(row))
            except Exception:  # pragma: no cover - defensive
                return False

        def get(self, cond: TinyDBQueryLike) -> Mapping[str, Any] | None:
            for row in self._rows:
                if self._matches(cond, row):
                    return dict(row)
            return None

        def insert(self, item: Mapping[str, Any]) -> int:
            self._rows.append(dict(item))
            return len(self._rows) - 1

        def update(self, fields: Mapping[str, Any], cond: TinyDBQueryLike) -> list[int]:
            updated: list[int] = []
            for idx, row in enumerate(self._rows):
                if self._matches(cond, row):
                    row.update(dict(fields))
                    updated.append(idx)
            return updated

        def remove(self, cond: TinyDBQueryLike) -> list[int]:
            removed: list[int] = []
            remaining: list[MutableMapping[str, Any]] = []
            for idx, row in enumerate(self._rows):
                if self._matches(cond, row):
                    removed.append(idx)
                else:
                    remaining.append(row)
            self._rows = remaining
            return removed

        def all(self) -> list[Mapping[str, Any]]:
            return [dict(row) for row in self._rows]

        def search(self, cond: TinyDBQueryLike) -> list[Mapping[str, Any]]:
            return [dict(row) for row in self._rows if self._matches(cond, row)]

        def truncate(self) -> None:
            self._rows.clear()

    class _TinyDB(TinyDBLike):
        def __init__(self, path: str, storage: object | None = None) -> None:
            self.path = path
            self._storage = storage
            self._tables: dict[str, _TinyDBTable] = {"_default": _TinyDBTable()}
            if callable(
                storage
            ):  # pragma: no cover - storage initialization side effect
                try:
                    storage(path)
                except TypeError:
                    storage(path=path)

        def table(self, name: str) -> _TinyDBTable:
            return self._tables.setdefault(name, _TinyDBTable())

        def close(self) -> None:
            return None

        # Convenience helpers mirroring TinyDB's default table proxy.
        def insert(self, item: Mapping[str, Any]) -> int:
            return self.table("_default").insert(item)

        def upsert(self, item: Mapping[str, Any], cond: TinyDBQueryLike) -> list[int]:
            updated = self.table("_default").update(item, cond)
            if updated:
                return updated
            return [self.table("_default").insert(item)]

        def get(self, cond: TinyDBQueryLike) -> Mapping[str, Any] | None:
            return self.table("_default").get(cond)

        def remove(self, cond: TinyDBQueryLike) -> list[int]:
            return self.table("_default").remove(cond)

        def all(self) -> list[Mapping[str, Any]]:
            return self.table("_default").all()

        def search(self, cond: TinyDBQueryLike) -> list[Mapping[str, Any]]:
            return self.table("_default").search(cond)

        def update(self, fields: Mapping[str, Any], cond: TinyDBQueryLike) -> list[int]:
            return self.table("_default").update(fields, cond)

        def truncate(self) -> None:
            self.table("_default").truncate()

    class TinyDB(_TinyDB):
        def __init__(self, path: str, storage: object | None = None, **_: Any) -> None:
            super().__init__(path, storage)

    def Query() -> TinyDBQueryLike:
        return _TinyDBQuery()

    class _Storage:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._args = args
            self._kwargs = kwargs

        def close(self) -> None:
            return None

    class JSONStorage(_Storage):
        def read(self) -> dict[str, dict[str, object]] | None:
            return {}

        def write(self, data: Mapping[str, Any]) -> None:
            _ = data

    class Storage(_Storage):
        pass

    def touch(path: str, create_dirs: bool = False) -> None:  # noqa: ARG001
        return None

    class CachingMiddleware:
        def __init__(self, factory: Callable[..., object]) -> None:
            self._factory = factory

        def __call__(self, *args: Any, **kwargs: Any) -> object:
            return self._factory(*args, **kwargs)

    storages_module = ModuleType("tinydb.storages")
    storages_module.JSONStorage = JSONStorage  # type: ignore[attr-defined]
    storages_module.Storage = Storage  # type: ignore[attr-defined]
    storages_module.touch = touch  # type: ignore[attr-defined]

    middlewares_module = ModuleType("tinydb.middlewares")
    middlewares_module.CachingMiddleware = CachingMiddleware  # type: ignore[attr-defined]

    module.TinyDB = TinyDB  # type: ignore[attr-defined]
    module.Query = Query  # type: ignore[attr-defined]
    module.storages = storages_module  # type: ignore[attr-defined]
    module.middlewares = middlewares_module  # type: ignore[attr-defined]

    sys.modules.setdefault("tinydb.storages", storages_module)
    sys.modules.setdefault("tinydb.middlewares", middlewares_module)
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

        def search(
            self, query: np.ndarray, top_k: int
        ) -> tuple[np.ndarray, np.ndarray]:
            if query.size == 0:
                return np.zeros((1, 0), dtype=np.float32), np.zeros(
                    (1, 0), dtype=np.int64
                )
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
_install_stub("tinydb", _build_tinydb_stub)
_install_stub("kuzu", _build_kuzu_stub)
_install_stub("faiss", _build_faiss_stub)

_TYPED_BUILD_MEMORY_RECORD = cast(MemoryRecordFactory, build_memory_record)


@pytest.fixture(autouse=True)
def _set_memory_resource_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure optional memory backends are treated as available in tests."""

    for resource in ("CHROMADB", "KUZU", "DUCKDB", "FAISS", "TINYDB"):
        monkeypatch.setenv(f"DEVSYNTH_RESOURCE_{resource}_AVAILABLE", "1")


@pytest.fixture(autouse=True)
def _reset_duckdb_stub_state() -> None:
    """Isolate DuckDB stub data between tests while preserving per-test flows."""

    _DUCKDB_DATA.clear()
    yield
    _DUCKDB_DATA.clear()


if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from devsynth.domain.interfaces.memory import (
        ContextManager,
        MemoryStore,
        VectorStore,
    )
else:

    class MemoryStore(Protocol):
        def store(self, item: MemoryItem) -> str: ...

        def retrieve(self, item_id: str) -> MemoryItem | MemoryRecord | None: ...

        def search(
            self, query: MemorySearchQuery | MemoryMetadata
        ) -> list[MemoryRecord]: ...

        def delete(self, item_id: str) -> bool: ...

        def begin_transaction(self) -> str: ...

        def commit_transaction(self, transaction_id: str) -> bool: ...

        def rollback_transaction(self, transaction_id: str) -> bool: ...

        def is_transaction_active(self, transaction_id: str) -> bool: ...

    class VectorStore(Protocol):
        def store_vector(self, vector: MemoryVector) -> str: ...

        def retrieve_vector(
            self, vector_id: str
        ) -> MemoryVector | MemoryRecord | None: ...

        def similarity_search(
            self, query_embedding: EmbeddingVector, top_k: int = 5
        ) -> list[MemoryRecord]: ...

        def delete_vector(self, vector_id: str) -> bool: ...

        def get_collection_stats(self) -> VectorStoreStats: ...

    class ContextManager(Protocol):
        def add_to_context(self, key: str, value: ContextValue) -> None: ...

        def get_from_context(self, key: str) -> ContextValue | None: ...

        def get_full_context(self) -> ContextState: ...

        def clear_context(self) -> None: ...


class ProtocolCompliantMemoryStore(MemoryStore):
    """In-memory ``MemoryStore`` implementation satisfying the protocol."""

    supports_transactions: bool = True

    def __init__(self, *args: object, **kwargs: object) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._active_transactions: set[str] = set()

    def store(self, item: MemoryItem) -> str:
        if not item.id:
            item.id = str(uuid.uuid4())
        record = _TYPED_BUILD_MEMORY_RECORD(item)
        self._records[item.id] = record
        return item.id

    def retrieve(self, item_id: str) -> MemoryRecord | None:
        return self._records.get(item_id)

    def search(self, query: MemorySearchQuery | MemoryMetadata) -> list[MemoryRecord]:
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
        self._records[vector.id] = _TYPED_BUILD_MEMORY_RECORD(
            vector, source="vector-fixture"
        )
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

    def get_collection_stats(self) -> VectorStoreStats:
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
    "GroupedMemoryResults",
    "MemoryMetadata",
    "MemoryQueryResults",
    "MemoryRecord",
    "MemoryRecordFactory",
    "MemorySearchQuery",
    "ProtocolCompliantContextManager",
    "ProtocolCompliantMemoryStore",
    "ProtocolCompliantVectorStore",
    "build_memory_record",
    "memory_record_factory",
    "memory_item",
    "memory_vector",
    "memory_record",
    "memory_query_results",
    "grouped_memory_results",
    "protocol_memory_store",
    "protocol_vector_store",
    "protocol_context_manager",
]


@pytest.fixture
def memory_record_factory() -> MemoryRecordFactory:
    """Expose :func:`build_memory_record` with preserved typing."""

    return _TYPED_BUILD_MEMORY_RECORD


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

    record = _TYPED_BUILD_MEMORY_RECORD(
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
