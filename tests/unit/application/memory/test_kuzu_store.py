import shutil
from concurrent.futures import ThreadPoolExecutor

import pytest

from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.domain.models.memory import MemoryItem, MemoryType


pytestmark = pytest.mark.requires_resource("kuzu")


@pytest.fixture(autouse=True)
def _patch_kuzu(monkeypatch):
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())


@pytest.fixture
def fallback_store(tmp_path):
    return KuzuStore(str(tmp_path), use_embedded=False)


@pytest.mark.medium
def test_init_creates_directory(tmp_path):
    path = tmp_path / "store"
    store = KuzuStore(str(path), use_embedded=False)
    try:
        assert path.exists()
        assert store.file_path == str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.mark.medium
def test_store_and_retrieve_succeeds(fallback_store):
    store = fallback_store
    item = MemoryItem(id="a", content="hello", memory_type=MemoryType.WORKING)
    store.store(item)
    got = store.retrieve("a")
    assert got is not None
    assert got.content == "hello"


@pytest.mark.medium
def test_transaction_rollback_restores_snapshot(fallback_store):
    store = fallback_store
    original = MemoryItem(id="a", content="init", memory_type=MemoryType.WORKING)
    store.store(original)

    with pytest.raises(RuntimeError):
        with store.transaction():
            store.store(
                MemoryItem(id="a", content="updated", memory_type=MemoryType.WORKING)
            )
            raise RuntimeError("boom")

    retrieved = store.retrieve("a")
    assert retrieved is not None
    assert retrieved.content == "init"


@pytest.mark.medium
def test_concurrent_transactions(fallback_store):
    store = fallback_store

    def write(idx: int) -> None:
        with store.transaction():
            store.store(
                MemoryItem(
                    id=f"{idx}", content=f"c{idx}", memory_type=MemoryType.WORKING
                )
            )

    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(write, range(10)))

    for i in range(10):
        assert store.retrieve(str(i)) is not None
