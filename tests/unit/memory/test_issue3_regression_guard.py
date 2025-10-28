"""Targeted regression guard for Issue 3 covering strict typed memory stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

import pytest

from devsynth.memory.sync_manager import SyncManager


@dataclass
class InMemoryStore:
    """Minimal MemoryStore implementation for SyncManager regression tests."""

    name: str
    data: dict[str, Any] = field(default_factory=dict)

    def write(self, key: str, value: Any) -> None:
        self.data[key] = value

    def read(self, key: str) -> Any:
        if key not in self.data:
            raise KeyError(key)
        return self.data[key]

    def snapshot(self) -> dict[str, Any]:
        return dict(self.data)

    def restore(self, snapshot: dict[str, Any]) -> None:
        self.data = dict(snapshot)


@pytest.fixture()
def sync_manager() -> SyncManager:
    stores = {
        name: InMemoryStore(name) for name in ("tinydb", "duckdb", "lmdb", "kuzu")
    }
    return SyncManager(stores)


@pytest.mark.fast
def test_issue3_findings_persist(sync_manager: SyncManager) -> None:
    """Regression guard: Issue 3 findings survive strict typed memory writes."""

    payload = {"id": "Issue 3", "summary": "merged without regression"}
    with sync_manager.transaction():
        sync_manager.write(payload["id"], payload)

    for store in sync_manager.stores.values():
        assert payload["id"] in store.snapshot()
        assert store.read(payload["id"]) == payload
