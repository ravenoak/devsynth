"""Basic tests for :class:`KuzuStore`."""
import tempfile
import shutil
import importlib.util
from pathlib import Path
from devsynth.domain.models.memory import MemoryItem, MemoryType

# Load module without triggering package imports
spec = importlib.util.spec_from_file_location(
    "kuzu_store", Path(__file__).resolve().parents[2] / "src/devsynth/application/memory/kuzu_store.py"
)
kuzu_store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kuzu_store)
KuzuStore = kuzu_store.KuzuStore


def test_store_retrieve_and_versions():
    temp_dir = tempfile.mkdtemp()
    store = KuzuStore(temp_dir)
    item = MemoryItem(id="a", content="hello", memory_type=MemoryType.WORKING)
    store.store(item)
    item2 = MemoryItem(id="a", content="hello2", memory_type=MemoryType.WORKING)
    store.store(item2)
    retrieved = store.retrieve("a")
    versions = store.get_versions("a")
    shutil.rmtree(temp_dir)
    assert retrieved.content == "hello2"
    assert len(versions) == 1


def test_search_by_metadata():
    temp_dir = tempfile.mkdtemp()
    store = KuzuStore(temp_dir)
    store.store(MemoryItem(id="1", content="alpha", memory_type=MemoryType.WORKING, metadata={"tag": "x"}))
    store.store(MemoryItem(id="2", content="beta", memory_type=MemoryType.WORKING, metadata={"tag": "y"}))
    results = store.search({"metadata.tag": "y"})
    shutil.rmtree(temp_dir)
    assert len(results) == 1
    assert results[0].id == "2"
