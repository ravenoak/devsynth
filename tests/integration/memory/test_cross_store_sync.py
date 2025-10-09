"""Integration tests for memory persistence, retrieval, and cross-store sync.

These tests exercise a minimal in-memory implementation of the MemoryStore
Protocol to validate expected behaviors without requiring optional extras
(e.g., ChromaDB, LMDB, FAISS, Kuzu). This expands integration coverage per
Docs Task 11.3: "Expand integration tests for persistence/retrieval/cross-store sync."

Style: Follows DevSynth testing guidelines (deterministic, no network, explicit
markers, clear Arrange-Act-Assert steps) and project guidelines principles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pytest

from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from tests.conftest import is_resource_available
from tests.fixtures.resources import (
    OPTIONAL_BACKEND_REQUIREMENTS,
    backend_import_reason,
    backend_skip_reason,
)

pytestmark = [pytest.mark.integration]


@dataclass
class _TxnState:
    ops: list[tuple[str, Any]]
    active: bool = True


class InMemoryStore(MemoryStore):
    """A minimal in-memory MemoryStore used for integration testing.

    - Implements basic CRUD and a toy transaction log with commit/rollback.
    - Deterministic behavior; no external state.
    """

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}
        self._txns: dict[str, _TxnState] = {}
        self._next_id = 1

    def _generate_id(self) -> str:
        val = str(self._next_id)
        self._next_id += 1
        return val

    # MemoryStore API
    def store(self, item: MemoryItem) -> str:
        if not item.id:
            item.id = self._generate_id()  # type: ignore[attr-defined]
        self._items[item.id] = item
        return item.id

    def retrieve(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def search(self, query: dict[str, Any]) -> list[MemoryItem]:
        # Minimal search: filter by memory_type or metadata exact matches
        results = list(self._items.values())
        if "memory_type" in query:
            mt = query["memory_type"]
            results = [i for i in results if i.memory_type == mt]
        for k, v in query.items():
            if k == "memory_type":
                continue
            results = [i for i in results if i.metadata.get(k) == v]
        return results

    def delete(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    # Transactions (toy implementation for contract coverage)
    def begin_transaction(self) -> str:
        txid = f"tx-{len(self._txns)+1}"
        self._txns[txid] = _TxnState(ops=[])
        return txid

    def commit_transaction(self, transaction_id: str) -> bool:
        state = self._txns.get(transaction_id)
        if not state or not state.active:
            return False
        # In a real store, we'd apply buffered ops; here we just mark complete.
        state.active = False
        return True

    def rollback_transaction(self, transaction_id: str) -> bool:
        state = self._txns.get(transaction_id)
        if not state or not state.active:
            return False
        # Undo any ops from the txn log
        for op, payload in reversed(state.ops):
            if op == "store":
                self._items.pop(payload, None)
            elif op == "delete":
                item: MemoryItem = payload
                self._items[item.id] = item
        state.active = False
        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        state = self._txns.get(transaction_id)
        return bool(state and state.active)


def sync_stores(source: MemoryStore, dest: MemoryStore) -> int:
    """Copy all items from source into dest if not present; return count.

    This is a simplified stand-in for a cross-store sync manager to validate
    that basic cross-store semantics are achievable without optional backends.
    """
    count = 0
    # Pull everything from source via a neutral query
    for item in source.search({}):
        if dest.retrieve(item.id) is None:
            # clone to avoid shared object references
            clone = MemoryItem(
                id=item.id,
                content=item.content,
                memory_type=item.memory_type,
                metadata=dict(item.metadata),
            )
            dest.store(clone)
            count += 1
    return count


@pytest.mark.medium
def test_store_and_retrieve_round_trip() -> None:
    # Arrange
    store = InMemoryStore()
    item = MemoryItem(
        id="",
        content={"text": "hello"},
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"k": 1},
    )

    # Act
    item_id = store.store(item)
    fetched = store.retrieve(item_id)

    # Assert
    assert fetched is not None
    assert fetched.content == {"text": "hello"}
    assert fetched.metadata["k"] == 1


@pytest.mark.medium
def test_search_by_memory_type_and_metadata_filters() -> None:
    store = InMemoryStore()
    store.store(
        MemoryItem(
            id="", content="a", memory_type=MemoryType.CONTEXT, metadata={"tag": "x"}
        )
    )
    store.store(
        MemoryItem(
            id="", content="b", memory_type=MemoryType.KNOWLEDGE, metadata={"tag": "x"}
        )
    )
    store.store(
        MemoryItem(
            id="", content="c", memory_type=MemoryType.KNOWLEDGE, metadata={"tag": "y"}
        )
    )

    results = store.search({"memory_type": MemoryType.KNOWLEDGE, "tag": "x"})
    assert [r.content for r in results] == ["b"]


@pytest.mark.medium
def test_delete_removes_item() -> None:
    store = InMemoryStore()
    item_id = store.store(
        MemoryItem(id="", content="gone", memory_type=MemoryType.CONTEXT, metadata={})
    )
    assert store.retrieve(item_id) is not None

    removed = store.delete(item_id)
    assert removed is True
    assert store.retrieve(item_id) is None


@pytest.mark.medium
def test_transactions_commit_and_rollback() -> None:
    store = InMemoryStore()
    txid = store.begin_transaction()
    assert store.is_transaction_active(txid)

    # store within a transaction context (record operation manually to emulate logging)
    item_id = store.store(
        MemoryItem(id="", content="t", memory_type=MemoryType.CONTEXT, metadata={})
    )
    store._txns[txid].ops.append(("store", item_id))  # type: ignore[attr-defined]

    # rollback should undo stored item
    assert store.rollback_transaction(txid)
    assert not store.is_transaction_active(txid)
    assert store.retrieve(item_id) is None

    # commit path (no ops to apply in this toy impl)
    txid2 = store.begin_transaction()
    assert store.is_transaction_active(txid2)
    assert store.commit_transaction(txid2)
    assert not store.is_transaction_active(txid2)


@pytest.mark.medium
def test_cross_store_sync_copies_missing_items() -> None:
    # Arrange
    src = InMemoryStore()
    dst = InMemoryStore()
    a_id = src.store(
        MemoryItem(
            id="",
            content="alpha",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"origin": "src"},
        )
    )
    b_id = src.store(
        MemoryItem(
            id="",
            content="beta",
            memory_type=MemoryType.CONTEXT,
            metadata={"origin": "src"},
        )
    )

    # Precondition: dest empty
    assert dst.retrieve(a_id) is None and dst.retrieve(b_id) is None

    # Act
    copied = sync_stores(src, dst)

    # Assert
    assert copied == 2
    assert dst.retrieve(a_id) is not None
    assert dst.retrieve(b_id) is not None
    # Ensure metadata preserved
    assert dst.retrieve(a_id).metadata["origin"] == "src"  # type: ignore[union-attr]


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.requires_resource("chromadb")
def test_cross_store_sync_with_chromadb_if_available(tmp_path, monkeypatch):
    """Cross-store sync using ChromaDBMemoryStore when chromadb extra is present.

    Skips if chromadb is not installed. Provider system is disabled to avoid any
    network usage; default embedding or no-embed path should suffice.
    """
    chroma_extras = tuple(OPTIONAL_BACKEND_REQUIREMENTS["chromadb"]["extras"])
    if not is_resource_available("chromadb"):
        pytest.skip(backend_skip_reason("chromadb", chroma_extras))
    pytest.importorskip(
        "chromadb",
        reason=backend_import_reason("chromadb"),
    )

    ChromaDBMemoryStore = pytest.importorskip(
        "devsynth.adapters.chromadb_memory_store",
        reason=backend_import_reason("chromadb"),
    ).ChromaDBMemoryStore

    # Ensure isolation in tests and no file logging noise
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")

    # Arrange
    src = InMemoryStore()
    dst = ChromaDBMemoryStore(
        persist_directory=str(tmp_path / "chroma"),
        use_provider_system=False,  # do not require any external provider
        collection_name="test_sync",
        instance_id="sync_case",
    )

    try:
        a_id = src.store(
            MemoryItem(
                id="",
                content="alpha",
                memory_type=MemoryType.KNOWLEDGE,
                metadata={"origin": "src"},
            )
        )
        b_id = src.store(
            MemoryItem(
                id="",
                content="beta",
                memory_type=MemoryType.CONTEXT,
                metadata={"origin": "src"},
            )
        )

        # Precondition: destination initially empty
        assert dst.retrieve(a_id) is None and dst.retrieve(b_id) is None

        # Act: copy by simple iteration (no embeddings required for existence check)
        copied = 0
        for item in src.search({}):
            if dst.retrieve(item.id) is None:
                dst.store(item)
                copied += 1

        # Assert
        assert copied == 2
        assert dst.retrieve(a_id) is not None
        assert dst.retrieve(b_id) is not None
    finally:
        # Best-effort cleanup to release ChromaDB resources
        try:
            dst.close()
        except Exception:
            pass
