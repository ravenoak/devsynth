"""Transaction rollback behaviour for the sync manager."""

from dataclasses import dataclass, field

import pytest

from devsynth.memory import SyncManager


@dataclass
class DummyStore:
    data: dict[str, str] = field(default_factory=dict)
    fail_on: str | None = None

    def write(self, key: str, value: str) -> None:
        if key == self.fail_on:
            raise RuntimeError("boom")
        self.data[key] = value

    def read(self, key: str) -> str:
        return self.data[key]

    def snapshot(self) -> dict[str, str]:
        return self.data.copy()

    def restore(self, snap: dict[str, str]) -> None:
        self.data = snap


@pytest.mark.fast
def test_transaction_rolls_back_all_stores() -> None:
    """A failing store causes rollback in every adapter.

    ReqID: FR-60
    """

    stores = {
        "tinydb": DummyStore(),
        "duckdb": DummyStore(),
        "lmdb": DummyStore(fail_on="bad"),
        "kuzu": DummyStore(),
    }
    manager = SyncManager(stores)

    with pytest.raises(RuntimeError):
        with manager.transaction():
            manager.write("ok", "1")
            manager.write("bad", "2")

    for store in stores.values():
        assert store.data == {}
