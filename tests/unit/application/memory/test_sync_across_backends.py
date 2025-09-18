import pytest

from tests.fixtures.resources import resource_flag_enabled

if not resource_flag_enabled("chromadb"):
    pytest.skip(
        "ChromaDB resource not enabled via DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE",
        allow_module_level=True,
    )

if not resource_flag_enabled("kuzu"):
    pytest.skip(
        "Kuzu resource not enabled via DEVSYNTH_RESOURCE_KUZU_AVAILABLE",
        allow_module_level=True,
    )

pytest.importorskip("chromadb")
from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.application.memory.sync_manager import SyncManager
from devsynth.application.memory.tinydb_store import TinyDBStore
from devsynth.domain.models.memory import MemoryItem, MemoryType


pytestmark = [
    pytest.mark.requires_resource("chromadb"),
    pytest.mark.requires_resource("kuzu"),
]


@pytest.fixture
def stores(tmp_path, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_NO_FILE_LOGGING", "1")
    monkeypatch.setenv("ENABLE_CHROMADB", "1")
    ef = pytest.importorskip("chromadb.utils.embedding_functions")

    monkeypatch.setattr(ef, "DefaultEmbeddingFunction", lambda: lambda x: [0.0] * 5)
    monkeypatch.setattr(KuzuMemoryStore, "__abstractmethods__", frozenset())
    monkeypatch.setattr(KuzuStore, "__abstractmethods__", frozenset())
    tiny = TinyDBStore(str(tmp_path / "tiny"))
    kuzu = KuzuMemoryStore.create_ephemeral()
    chroma = ChromaDBStore(str(tmp_path / "chroma"))
    yield (tiny, kuzu, chroma)
    kuzu.cleanup()


def _manager(tiny, kuzu, chroma, async_mode=False):
    adapters = {"tinydb": tiny, "kuzu": kuzu, "chroma": chroma}
    manager = MemoryManager(adapters=adapters)
    manager.sync_manager = SyncManager(manager, async_mode=async_mode)
    return manager


@pytest.mark.medium
def test_basic_synchronization_succeeds(stores):
    tiny, kuzu, chroma = stores
    manager = _manager(tiny, kuzu, chroma)
    item = MemoryItem(id="a", content="A", memory_type=MemoryType.CODE)
    tiny.store(item)
    manager.synchronize("tinydb", "kuzu")
    assert kuzu.retrieve("a") is not None
    manager.synchronize("kuzu", "chroma")
    assert chroma.retrieve("a") is not None


@pytest.mark.medium
def test_conflict_detection_and_resolution(stores):
    tiny, kuzu, _ = stores
    manager = _manager(tiny, kuzu, stores[2])
    older = MemoryItem(id="c", content="old", memory_type=MemoryType.CODE)
    kuzu.store(older)
    newer = MemoryItem(id="c", content="new", memory_type=MemoryType.CODE)
    tiny.store(newer)
    manager.synchronize("tinydb", "kuzu")
    resolved = kuzu.retrieve("c")
    assert resolved.content == "new"
    assert manager.sync_manager.stats["conflicts"] == 1


@pytest.mark.asyncio
@pytest.mark.medium
async def test_async_queue_flush_succeeds(stores):
    tiny, kuzu, _ = stores
    manager = _manager(tiny, kuzu, stores[2], async_mode=True)
    item = MemoryItem(id="async1", content="A", memory_type=MemoryType.CODE)
    manager.sync_manager.queue_update("tinydb", item)
    await manager.sync_manager.wait_for_async()
    assert kuzu.retrieve("async1") is not None
