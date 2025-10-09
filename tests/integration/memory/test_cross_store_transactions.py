import sys

"""Integration tests verifying cross-store transaction DTO typing."""

# mypy: ignore-errors

import sys
from typing import TYPE_CHECKING, Any, TypeAlias, cast

import pytest

from tests.fixtures.resources import skip_if_missing_backend

if TYPE_CHECKING:
    from devsynth.adapters.kuzu_memory_store import (
        KuzuMemoryStore as KuzuMemoryStoreClass,
    )
    from devsynth.application.memory.faiss_store import FAISSStore as FAISSStoreClass
    from devsynth.application.memory.kuzu_store import KuzuStore as KuzuStoreClass
    from devsynth.application.memory.lmdb_store import LMDBStore as LMDBStoreClass

    LMDBStore = LMDBStoreClass
    FAISSStore = FAISSStoreClass
    KuzuMemoryStore = KuzuMemoryStoreClass
    KuzuStore = KuzuStoreClass

    LMDBStoreType: TypeAlias = LMDBStoreClass
    FAISSStoreType: TypeAlias = FAISSStoreClass
    KuzuMemoryStoreType: TypeAlias = KuzuMemoryStoreClass
    KuzuStoreType: TypeAlias = KuzuStoreClass
else:
    importorskip = getattr(pytest, "importorskip")

    LMDBStore = cast(
        Any,
        importorskip(
            "devsynth.application.memory.lmdb_store",
            reason="Install the 'memory' or 'tests' extras to enable LMDB-backed tests.",
        ).LMDBStore,
    )
    FAISSStore = cast(
        Any,
        importorskip(
            "devsynth.application.memory.faiss_store",
            reason="Install the 'retrieval' or 'memory' extras to enable FAISS-backed tests.",
        ).FAISSStore,
    )
    KuzuMemoryStore = cast(
        Any,
        importorskip(
            "devsynth.adapters.kuzu_memory_store",
            reason="Install the 'retrieval' or 'memory' extras to enable Kuzu-backed tests.",
        ).KuzuMemoryStore,
    )
    KuzuStore = cast(
        Any,
        importorskip(
            "devsynth.application.memory.kuzu_store",
            reason="Install the 'retrieval' or 'memory' extras to enable Kuzu-backed tests.",
        ).KuzuStore,
    )

    LMDBStoreType = Any
    FAISSStoreType = Any
    KuzuMemoryStoreType = Any
    KuzuStoreType = Any
from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.sync_manager import SyncManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

pytestmark = [
    *skip_if_missing_backend("lmdb"),
    *skip_if_missing_backend("faiss"),
]


# type: ignore[arg-type]
@pytest.fixture(autouse=True)
def no_kuzu(monkeypatch: Any) -> None:
    monkeypatch.delitem(sys.modules, "kuzu", raising=False)
    for cls in (KuzuMemoryStore, KuzuStore, LMDBStore, FAISSStore):
        monkeypatch.setattr(cls, "__abstractmethods__", frozenset())


def _manager(
    lmdb: LMDBStoreType, faiss: FAISSStoreType, kuzu: KuzuMemoryStoreType
) -> MemoryManager:
    adapters = {"lmdb": lmdb, "faiss": faiss, "kuzu": kuzu}
    manager = MemoryManager(adapters=adapters)
    manager.sync_manager = SyncManager(manager)
    return manager


@pytest.mark.medium
def test_cross_store_transaction_commit(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="1", content="hello", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="1", content="hello", embedding=[0.1] * 5, metadata={})

    with manager.sync_manager.transaction(["lmdb", "faiss", "kuzu"]):
        lmdb.store(item)
        faiss.store_vector(vector)
        kuzu.store(item)

    assert lmdb.retrieve("1") is not None
    assert faiss.retrieve_vector("1") is not None
    assert kuzu.retrieve("1") is not None
    assert kuzu.retrieve_vector("1") is not None

    kuzu.cleanup()  # type: ignore[unreachable]


@pytest.mark.medium
def test_cross_store_query_emits_typed_results(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="5", content="typed", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="5", content="typed", embedding=[0.5] * 5, metadata={})

    with manager.sync_manager.transaction(["lmdb", "faiss", "kuzu"]):
        lmdb.store(item)
        faiss.store_vector(vector)
        kuzu.store(item)

    grouped = manager.sync_manager.cross_store_query("typed")

    assert grouped["query"] == "typed"
    assert set(grouped["by_store"].keys()) == {"lmdb", "faiss", "kuzu"}

    faiss_records = grouped["by_store"]["faiss"]["records"]
    lmdb_records = grouped["by_store"]["lmdb"]["records"]
    kuzu_records = grouped["by_store"]["kuzu"]["records"]

    for records in (faiss_records, lmdb_records, kuzu_records):
        assert records and all(isinstance(record, MemoryRecord) for record in records)

    combined = grouped.get("combined")
    assert combined is not None
    assert all(isinstance(record, MemoryRecord) for record in combined)

    sources = {record.source for record in combined}
    assert sources == {"lmdb", "faiss", "kuzu"}

    kuzu.cleanup()  # type: ignore[unreachable]


@pytest.mark.medium
def test_cross_store_transaction_rollback(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    lmdb = LMDBStore(str(tmp_path / "lmdb"))
    faiss = FAISSStore(str(tmp_path / "faiss"))
    kuzu = KuzuMemoryStore.create_ephemeral(use_provider_system=False)
    manager = _manager(lmdb, faiss, kuzu)

    item = MemoryItem(id="2", content="world", memory_type=MemoryType.CODE)
    vector = MemoryVector(id="2", content="world", embedding=[0.2] * 5, metadata={})

    with pytest.raises(RuntimeError):
        with manager.sync_manager.transaction(["lmdb", "faiss", "kuzu"]):
            lmdb.store(item)
            faiss.store_vector(vector)
            kuzu.store(item)
            raise RuntimeError("boom")

    assert lmdb.retrieve("2") is None
    assert faiss.retrieve_vector("2") is None
    assert kuzu.retrieve("2") is None
    assert kuzu.retrieve_vector("2") is None

    kuzu.cleanup()  # type: ignore[unreachable]
