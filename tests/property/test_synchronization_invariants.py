"""Property tests for the synchronization invariants.

DocRef: docs/analysis/synchronization_algorithm_proof.md
"""

from __future__ import annotations

import uuid
from dataclasses import replace
from typing import Dict, Tuple

import pytest

try:  # pragma: no cover - Hypothesis is optional
    from hypothesis import assume, given, settings
    from hypothesis import strategies as st
except Exception:  # pragma: no cover - skip when Hypothesis missing
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.application.memory.memory_integration import MemoryIntegrationManager
from devsynth.domain.models.memory import MemoryItem, MemoryType


class _DummyMemoryStore:
    """Minimal in-memory store implementing the MemoryStore protocol."""

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}
        self._active_transactions: set[str] = set()

    # MemoryStore protocol -------------------------------------------------
    def store(self, item: MemoryItem) -> str:
        cloned = replace(item, metadata=dict(item.metadata))
        self._items[cloned.id] = cloned
        return cloned.id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        item = self._items.get(item_id)
        if item is None:
            return None
        return replace(item, metadata=dict(item.metadata))

    def search(self, query: dict[str, object] | None = None) -> list[MemoryItem]:
        return list(self._items.values())

    def delete(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def begin_transaction(self) -> str:
        txn_id = str(uuid.uuid4())
        self._active_transactions.add(txn_id)
        return txn_id

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

    # Helpers --------------------------------------------------------------
    def snapshot(self) -> dict[str, tuple[object, tuple[tuple[str, object], ...]]]:
        """Return deterministic state for equality checks."""

        snapshot: dict[str, tuple[object, tuple[tuple[str, object], ...]]] = {}
        for item in self._items.values():
            metadata_items = tuple(sorted(item.metadata.items()))
            snapshot[item.id] = (item.content, metadata_items)
        return snapshot


def _build_store(data: dict[str, object]) -> _DummyMemoryStore:
    store = _DummyMemoryStore()
    for key, value in data.items():
        store.store(
            MemoryItem(id=key, content=value, memory_type=MemoryType.SHORT_TERM)
        )
    return store


def _pending_updates(
    source: _DummyMemoryStore, target: _DummyMemoryStore
) -> dict[str, tuple[object, object | None]]:
    pending: dict[str, tuple[object, object | None]] = {}
    for item in source.search({}):
        candidate = target.retrieve(item.id)
        if candidate is None or candidate.content != item.content:
            pending[item.id] = (
                item.content,
                None if candidate is None else candidate.content,
            )
    return pending


@st.composite
def _store_states(draw: st.DrawFn) -> tuple[dict[str, int], dict[str, int]]:
    keys = draw(
        st.lists(
            st.text(
                min_size=1,
                max_size=6,
                alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            ),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    values = draw(st.lists(st.integers(), min_size=len(keys), max_size=len(keys)))
    source = dict(zip(keys, values))

    target: dict[str, int] = {}
    for key in keys:
        if draw(st.booleans()):
            if draw(st.booleans()):
                target[key] = source[key]
            else:
                alt = draw(st.integers())
                assume(alt != source[key])
                target[key] = alt
    return source, target


@pytest.mark.property
@pytest.mark.medium
@given(states=_store_states())
@settings(max_examples=50)
def test_synchronize_clears_pending_updates(
    states: tuple[dict[str, int], dict[str, int]],
) -> None:
    """Invariant: synchronize(A, B) yields B == A and P_A = ∅.

    ReqID: SYNC-INV-01
    """

    source_data, target_data = states
    store_a = _build_store(source_data)
    store_b = _build_store(target_data)

    manager = MemoryIntegrationManager()
    manager.register_memory_store("A", store_a)
    manager.register_memory_store("B", store_b)

    result = manager.synchronize_stores("A", "B", bidirectional=False)

    assert store_a.snapshot() == store_b.snapshot()
    assert _pending_updates(store_a, store_b) == {}
    assert result["A_to_B"] == len(source_data)
