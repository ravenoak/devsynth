"""Shared fixtures for memory adapter unit tests with typed DTOs."""

from __future__ import annotations

import importlib.util
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol, TYPE_CHECKING

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
