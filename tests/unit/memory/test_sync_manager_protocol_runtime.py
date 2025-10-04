"""Runtime protocol compatibility checks for :mod:`devsynth.memory.sync_manager`."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from devsynth.memory.sync_manager import MemoryStore, SyncManager


@dataclass(slots=True)
class IntStore:
    """Minimal ``MemoryStore`` stub storing integer payloads."""

    data: dict[str, int] = field(default_factory=dict)
    fail_on_key: str | None = None
    restores: int = 0

    def write(self, key: str, value: int) -> None:
        if key == self.fail_on_key:
            raise RuntimeError("boom")
        self.data[key] = value

    def read(self, key: str) -> int:
        return self.data[key]

    def snapshot(self) -> dict[str, int]:
        return dict(self.data)

    def restore(self, snapshot: dict[str, int]) -> None:
        self.restores += 1
        self.data = dict(snapshot)


def build_manager(*, failing_key: str | None = None) -> SyncManager[int]:
    stores = {
        name: IntStore(fail_on_key=failing_key if name == "lmdb" else None)
        for name in ("tinydb", "duckdb", "lmdb", "kuzu")
    }
    return SyncManager(stores)


@pytest.mark.fast
def test_stub_store_matches_protocol_runtime() -> None:
    """The stub satisfies :class:`MemoryStore` at runtime and sync persists values."""

    store = IntStore()
    assert isinstance(store, MemoryStore)

    manager = build_manager()
    with manager.transaction():
        manager.write("answer", 42)

    for backend in manager.stores.values():
        assert backend.read("answer") == 42
        assert backend.restores == 0


@pytest.mark.fast
def test_transaction_rolls_back_typed_stores() -> None:
    """A failure during the transaction restores each backend snapshot."""

    manager = build_manager(failing_key="fail")

    for backend in manager.stores.values():
        backend.write("seed", 7)

    with pytest.raises(RuntimeError):
        with manager.transaction():
            manager.write("seed", 8)
            manager.write("fail", 9)

    for backend in manager.stores.values():
        assert backend.read("seed") == 7
        assert backend.restores == 1
