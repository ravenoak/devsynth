import random
import uuid
from dataclasses import dataclass
from typing import Dict


@dataclass
class MemoryItem:
    """Minimal memory item used for simulation."""

    id: str
    content: str


class TransactionalStore:
    """Simple in-memory store with transactional snapshots."""

    def __init__(self) -> None:
        self.items: Dict[str, MemoryItem] = {}
        self._snapshots: Dict[str, Dict[str, MemoryItem]] = {}

    def store(self, item: MemoryItem) -> None:
        self.items[item.id] = item

    def delete(self, item_id: str) -> None:
        self.items.pop(item_id, None)

    def begin_transaction(self) -> str:
        tx_id = str(uuid.uuid4())
        self._snapshots[tx_id] = self.items.copy()
        return tx_id

    def commit_transaction(self, tx_id: str) -> bool:
        return self._snapshots.pop(tx_id, None) is not None

    def rollback_transaction(self, tx_id: str) -> bool:
        snapshot = self._snapshots.pop(tx_id, None)
        if snapshot is None:
            return False
        self.items = snapshot
        return True

    def is_transaction_active(self, tx_id: str) -> bool:
        return tx_id in self._snapshots


class SynchronizableStore(TransactionalStore):
    """Transactional store that can synchronize its state with a peer."""

    def sync_from(self, other: "SynchronizableStore") -> None:
        """Copy all items from ``other`` into this store."""
        self.items = other.items.copy()


def run_simulation(iterations: int = 100) -> None:
    store = TransactionalStore()
    for _ in range(iterations):
        start_state = store.items.copy()
        expected_state = start_state.copy()
        tx = store.begin_transaction()
        for _ in range(random.randint(1, 5)):
            if random.random() < 0.5 or not expected_state:
                item_id = str(uuid.uuid4())
                item = MemoryItem(id=item_id, content=f"item-{random.random()}")
                store.store(item)
                expected_state[item_id] = item
            else:
                victim = random.choice(list(expected_state.keys()))
                store.delete(victim)
                expected_state.pop(victim, None)
        if random.random() < 0.5:
            store.commit_transaction(tx)
            assert store.items == expected_state and not store.is_transaction_active(tx)
        else:
            store.rollback_transaction(tx)
            assert store.items == start_state and not store.is_transaction_active(tx)
    print(f"Simulation passed for {iterations} iterations")


def run_synchronization_simulation(iterations: int = 100) -> None:
    """Simulate synchronization between two replicas."""
    primary = SynchronizableStore()
    replica = SynchronizableStore()
    for _ in range(iterations):
        start_replica_state = replica.items.copy()
        tx = primary.begin_transaction()
        item_id = str(uuid.uuid4())
        primary.store(MemoryItem(id=item_id, content="data"))
        if random.random() < 0.5:
            primary.commit_transaction(tx)
            replica.sync_from(primary)
            assert replica.items == primary.items
        else:
            primary.rollback_transaction(tx)
            assert replica.items == start_replica_state
    print(f"Synchronization simulation passed for {iterations} iterations")


def main() -> None:  # pragma: no cover - manual execution
    run_simulation()
    run_synchronization_simulation()


if __name__ == "__main__":  # pragma: no cover - manual execution script
    main()
