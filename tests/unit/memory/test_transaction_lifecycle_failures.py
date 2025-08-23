import uuid
from dataclasses import dataclass

import pytest


@dataclass
class MemoryItem:
    id: str
    content: str


class TransactionalStore:
    def __init__(self) -> None:
        self.items: dict[str, MemoryItem] = {}
        self._snapshots: dict[str, dict[str, MemoryItem]] = {}

    def store(self, item: MemoryItem) -> None:
        self.items[item.id] = item

    def delete(self, item_id: str) -> None:
        self.items.pop(item_id, None)

    def begin_transaction(self) -> str:
        tx = str(uuid.uuid4())
        self._snapshots[tx] = self.items.copy()
        return tx

    def commit_transaction(self, tx: str) -> bool:
        return self._snapshots.pop(tx, None) is not None

    def rollback_transaction(self, tx: str) -> bool:
        snap = self._snapshots.pop(tx, None)
        if snap is None:
            return False
        self.items = snap
        return True

    def is_transaction_active(self, tx: str) -> bool:
        return tx in self._snapshots


@pytest.mark.fast
def test_commit_unknown_transaction_returns_false():
    """Commit fails for unknown transaction IDs.

    ReqID: FR-60"""
    store = TransactionalStore()
    item = MemoryItem(id=str(uuid.uuid4()), content="x")
    store.store(item)
    snapshot = store.items.copy()
    assert not store.commit_transaction("nope")
    assert store.items == snapshot
    assert not store.is_transaction_active("nope")


@pytest.mark.fast
def test_rollback_unknown_transaction_returns_false():
    """Rollback fails for unknown transaction IDs.

    ReqID: FR-60"""
    store = TransactionalStore()
    item = MemoryItem(id=str(uuid.uuid4()), content="x")
    store.store(item)
    snapshot = store.items.copy()
    assert not store.rollback_transaction("nope")
    assert store.items == snapshot
    assert not store.is_transaction_active("nope")


@pytest.mark.fast
def test_double_commit_fails_and_state_persists():
    """Second commit on same transaction is rejected.

    ReqID: FR-60"""
    store = TransactionalStore()
    tx = store.begin_transaction()
    item = MemoryItem(id=str(uuid.uuid4()), content="x")
    store.store(item)
    assert store.commit_transaction(tx)
    snapshot = store.items.copy()
    assert not store.commit_transaction(tx)
    assert store.items == snapshot
    assert not store.is_transaction_active(tx)
