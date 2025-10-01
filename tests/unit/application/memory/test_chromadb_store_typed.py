"""Typed integration tests for :mod:`devsynth.application.memory.chromadb_store`."""

from __future__ import annotations

from datetime import datetime, timedelta

import sys
import types

import pytest

sys.modules.pop("devsynth.domain.interfaces.memory", None)
interfaces_pkg = sys.modules.setdefault(
    "devsynth.domain.interfaces", types.ModuleType("devsynth.domain.interfaces")
)
memory_stub = types.ModuleType("devsynth.domain.interfaces.memory")

class _MemoryStore:
    def store(self, item): ...

    def retrieve(self, item_id): ...

    def search(self, query): ...

    def delete(self, item_id): ...

    def begin_transaction(self): ...

    def commit_transaction(self, transaction_id): ...

    def rollback_transaction(self, transaction_id): ...

    def is_transaction_active(self, transaction_id): ...


class _VectorStore:
    def store_vector(self, vector): ...

    def retrieve_vector(self, vector_id): ...

    def similarity_search(self, query_embedding, top_k=5): ...

    def delete_vector(self, vector_id): ...

    def get_collection_stats(self): ...


class _ContextManager:
    def add_to_context(self, key, value): ...

    def get_from_context(self, key): ...

    def get_full_context(self): ...

    def clear_context(self): ...


memory_stub.MemoryStore = _MemoryStore  # type: ignore[attr-defined]
memory_stub.VectorStore = _VectorStore  # type: ignore[attr-defined]
memory_stub.ContextManager = _ContextManager  # type: ignore[attr-defined]
sys.modules["devsynth.domain.interfaces.memory"] = memory_stub
setattr(interfaces_pkg, "memory", memory_stub)

sys.modules.pop("devsynth.application.memory.chromadb_store", None)

import devsynth.application.memory.chromadb_store as chromadb_module
from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.metadata_serialization import (
    from_serializable,
    to_serializable,
)
from devsynth.domain.models.memory import MemoryType


pytestmark = [
    pytest.mark.requires_resource("chromadb"),
]


@pytest.mark.fast
def test_search_normalizes_serialized_rows(tmp_path, monkeypatch):
    """``ChromaDBStore.search`` should normalize rows via serialization helpers."""

    store = ChromaDBStore(str(tmp_path))

    record_calls: dict[str, int] = {"record_from_row": 0, "query_results_from_rows": 0}

    original_record_from_row = chromadb_module.record_from_row
    original_query_results_from_rows = chromadb_module.query_results_from_rows

    def tracking_record_from_row(*args, **kwargs):
        record_calls["record_from_row"] += 1
        return original_record_from_row(*args, **kwargs)

    def tracking_query_results_from_rows(*args, **kwargs):
        record_calls["query_results_from_rows"] += 1
        return original_query_results_from_rows(*args, **kwargs)

    monkeypatch.setattr(
        chromadb_module,
        "record_from_row",
        tracking_record_from_row,
    )
    monkeypatch.setattr(
        chromadb_module,
        "query_results_from_rows",
        tracking_query_results_from_rows,
    )

    timestamp = datetime.now().replace(microsecond=0)
    nested_timestamp = timestamp + timedelta(minutes=5)
    serialized_metadata = to_serializable(
        {
            "timestamp": timestamp,
            "nested": {
                "when": nested_timestamp,
                "tags": ["alpha", nested_timestamp],
            },
            "count": 2,
        }
    )

    row_payload = {
        "id": "typed-id",
        "content": "typed content",
        "memory_type": MemoryType.CONTEXT.value,
        "metadata": serialized_metadata,
        "created_at": timestamp.isoformat(),
        "similarity": "0.42",
    }

    store._use_fallback = True
    store._store.clear()
    store._cache.clear()
    store._store[row_payload["id"]] = dict(row_payload)

    results = store.search({"content": "typed"})

    assert record_calls["query_results_from_rows"] == 1
    assert record_calls["record_from_row"] == 1

    assert results["store"] == f"{store.collection_name}-fallback"
    assert isinstance(results["records"], list)
    assert len(results["records"]) == 1

    record = results["records"][0]
    assert isinstance(record, MemoryRecord)
    assert record.source == f"{store.collection_name}-fallback"
    assert record.similarity == pytest.approx(0.42)

    expected_metadata = from_serializable(serialized_metadata)
    assert record.metadata == expected_metadata
    assert isinstance(record.metadata["timestamp"], datetime)
    nested_metadata = record.metadata["nested"]
    assert isinstance(nested_metadata, dict)
    assert isinstance(nested_metadata["when"], datetime)
    assert isinstance(nested_metadata["tags"], list)
    assert isinstance(nested_metadata["tags"][1], datetime)


@pytest.mark.fast
def test_fallback_retrieve_uses_serialization_helpers(tmp_path, monkeypatch):
    """Fallback retrieval should still normalize metadata and similarity."""

    store = ChromaDBStore(str(tmp_path))
    store._use_fallback = True
    store._store.clear()
    store._cache.clear()

    original_record_from_row = chromadb_module.record_from_row
    calls = {"record_from_row": 0}

    def tracking_record_from_row(*args, **kwargs):
        calls["record_from_row"] += 1
        return original_record_from_row(*args, **kwargs)

    monkeypatch.setattr(chromadb_module, "record_from_row", tracking_record_from_row)

    timestamp = datetime.now().replace(microsecond=0)
    serialized_metadata = to_serializable(
        {
            "timestamp": timestamp,
            "nested": {"depth": {"when": timestamp}},
            "values": [1, {"ts": timestamp}],
        }
    )

    payload = {
        "id": "fallback-id",
        "content": "cached",
        "memory_type": MemoryType.LONG_TERM.value,
        "metadata": serialized_metadata,
        "created_at": timestamp.isoformat(),
        "similarity": "1.0",
    }

    store._store[payload["id"]] = payload

    record = store.retrieve(payload["id"])

    assert calls["record_from_row"] == 1
    assert isinstance(record, MemoryRecord)
    assert record.source == f"{store.collection_name}-fallback"
    assert record.similarity == pytest.approx(1.0)

    expected_metadata = from_serializable(serialized_metadata)
    assert record.metadata == expected_metadata
    assert isinstance(record.metadata["timestamp"], datetime)
    nested_metadata = record.metadata["nested"]
    assert isinstance(nested_metadata, dict)
    assert isinstance(nested_metadata["depth"]["when"], datetime)
    value_list = record.metadata["values"]
    assert isinstance(value_list, list)
    assert isinstance(value_list[1], dict)
    assert isinstance(value_list[1]["ts"], datetime)
