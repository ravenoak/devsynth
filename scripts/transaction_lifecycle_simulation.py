"""Transactional memory lifecycle simulation with coverage reset demo."""

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
        self.items: dict[str, MemoryItem] = {}
        self._snapshots: dict[str, dict[str, MemoryItem]] = {}

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


@dataclass
class CoverageTracker:
    """Track executed line identifiers and support resets."""

    lines: set[int]

    def mark(self, line: int) -> None:
        self.lines.add(line)

    def reset(self) -> None:
        self.lines.clear()


def run_simulation(iterations: int = 100) -> None:
    store = TransactionalStore()
    coverage = CoverageTracker(lines=set())
    for _ in range(iterations):
        start_state = store.items.copy()
        expected_state = start_state.copy()
        tx = store.begin_transaction()
        for _ in range(random.randint(1, 5)):
            coverage.mark(random.randint(1, 1_000))
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
        coverage.reset()
        assert not coverage.lines
    print(f"Simulation passed for {iterations} iterations")


def main() -> None:  # pragma: no cover - manual execution
    run_simulation()


if __name__ == "__main__":  # pragma: no cover - manual execution script
    main()
