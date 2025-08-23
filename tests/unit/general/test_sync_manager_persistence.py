"""Integration test for cross-adapter persistence."""

from dataclasses import dataclass, field

import pytest

from devsynth.memory import SyncManager


@dataclass
class DummyStore:
    data: dict[str, str] = field(default_factory=dict)

    def write(self, key: str, value: str) -> None:
        self.data[key] = value

    def read(self, key: str) -> str:
        return self.data[key]

    def snapshot(self) -> dict[str, str]:
        return self.data.copy()

    def restore(self, snap: dict[str, str]) -> None:
        self.data = snap


@pytest.mark.fast
def test_sync_manager_persists_to_all_stores() -> None:
    """SyncManager writes propagate to every adapter.

    ReqID: FR-60
    """

    stores = {name: DummyStore() for name in ["tinydb", "duckdb", "lmdb", "kuzu"]}
    manager = SyncManager(stores)
    with manager.transaction():
        manager.write("key", "value")

    for store in stores.values():
        assert store.read("key") == "value"

    assert manager.read("key") == "value"
