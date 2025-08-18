import os
from datetime import datetime

import pytest

from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.application.memory.lmdb_store import LMDBStore
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType


def _make_store(store_cls, tmp_path, monkeypatch):
    if store_cls is TinyDBStore:
        return TinyDBStore(str(tmp_path))
    if store_cls is LMDBStore:
        return LMDBStore(str(tmp_path))
    if store_cls is KuzuStore:
        monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())
        return KuzuStore(str(tmp_path))
    if store_cls is ChromaDBStore:
        monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
        monkeypatch.setenv("ENABLE_CHROMADB", "1")
        return ChromaDBStore(str(tmp_path))
    raise ValueError(store_cls)


@pytest.mark.parametrize(
    "store_cls", [TinyDBStore, LMDBStore, KuzuStore, ChromaDBStore]
)
@pytest.mark.medium
def test_basic_crud_lifecycle(store_cls, tmp_path, monkeypatch):
    store = _make_store(store_cls, tmp_path, monkeypatch)
    try:
        item_id = "test-item" if store_cls in {KuzuStore, ChromaDBStore} else ""
        item = MemoryItem(
            id=item_id,
            content="hello",
            memory_type=MemoryType.WORKING,
            metadata={},
            created_at=datetime.now(),
        )
        item_id = store.store(item)
        assert item_id
        retrieved = store.retrieve(item_id)
        assert retrieved and retrieved.content == "hello"
        item.content = "updated"
        store.store(item)
        updated = store.retrieve(item_id)
        assert updated and updated.content == "updated"
        assert store.delete(item_id) is True
        assert store.retrieve(item_id) is None
    finally:
        if hasattr(store, "close"):
            store.close()
