import pytest

# Speed marker discipline: exactly one speed marker

pytestmark = pytest.mark.fast

"""
ReqID: FR-09; Plan: docs/plan.md Phase 2 (Adapters/Stores fast-path)
Purpose: Validate StorageAdapter protocol shape via a pure-Python dummy, without touching real backends.
This is a fast unit test and should never access network or optional deps.
"""

from typing import Any, Dict, List, Optional

from devsynth.application.memory.adapters.storage_adapter import StorageAdapter
from devsynth.domain.models.memory import MemoryItem


class _DummyStore(StorageAdapter):
    backend_type = "dummy"

    def __init__(self) -> None:
        self._data: dict[str, MemoryItem] = {}
        self._tx_active: dict[str, bool] = {}

    # MemoryStore protocol methods
    def store(self, item: MemoryItem) -> str:  # type: ignore[override]
        self._data[item.id] = item
        return item.id

    def retrieve(self, item_id: str) -> MemoryItem | None:  # type: ignore[override]
        return self._data.get(item_id)

    def search(self, query: dict[str, Any]) -> list[MemoryItem]:  # type: ignore[override]
        q = str(query.get("query", "")).lower()
        return [m for m in self._data.values() if q in str(m.content).lower()]

    def delete(self, item_id: str) -> bool:  # type: ignore[override]
        return self._data.pop(item_id, None) is not None

    # Transactional protocol (minimal/no-op-ish)
    def begin_transaction(self) -> str:  # type: ignore[override]
        tx = f"tx_{len(self._tx_active)}"
        self._tx_active[tx] = True
        return tx

    def commit_transaction(self, transaction_id: str) -> bool:  # type: ignore[override]
        return self._tx_active.pop(transaction_id, None) is not None

    def rollback_transaction(self, transaction_id: str) -> bool:  # type: ignore[override]
        return self._tx_active.pop(transaction_id, None) is not None

    def is_transaction_active(self, transaction_id: str) -> bool:  # type: ignore[override]
        return bool(self._tx_active.get(transaction_id))


def test_storage_adapter_protocol_shape() -> None:
    store = _DummyStore()

    # Protocol exposure
    assert getattr(_DummyStore, "backend_type", None) == "dummy"

    # Basic CRUD
    item = MemoryItem(id="1", content="Hello", memory_type="WORKING")
    stored_id = store.store(item)
    assert stored_id == "1"
    assert store.retrieve("1") is item

    # Search matches case-insensitively
    results = store.search({"query": "hel"})
    assert results and results[0].id == "1"

    # Delete
    assert store.delete("1") is True
    assert store.retrieve("1") is None

    # Transaction minimal behavior
    tx = store.begin_transaction()
    assert store.is_transaction_active(tx) is True
    assert store.commit_transaction(tx) is True
    assert store.is_transaction_active(tx) is False
