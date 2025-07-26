"""Basic tests for :class:`KuzuStore`."""
import importlib.util
from pathlib import Path
from devsynth.domain.models.memory import MemoryItem, MemoryType
spec = importlib.util.spec_from_file_location('kuzu_store', Path(__file__).
    resolve().parents[3] / 'src/devsynth/application/memory/kuzu_store.py')
kuzu_store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kuzu_store)
KuzuStore = kuzu_store.KuzuStore


def test_store_retrieve_and_versions_succeeds(tmp_path):
    """Test that store retrieve and versions succeeds.

ReqID: N/A"""
    store = KuzuStore(str(tmp_path))
    item = MemoryItem(id='a', content='hello', memory_type=MemoryType.WORKING)
    store.store(item)
    item2 = MemoryItem(id='a', content='hello2', memory_type=MemoryType.WORKING
        )
    store.store(item2)
    retrieved = store.retrieve('a')
    versions = store.get_versions('a')
    assert retrieved.content == 'hello2'
    assert len(versions) == 1


def test_search_by_metadata_succeeds(tmp_path):
    """Test that search by metadata succeeds.

ReqID: N/A"""
    store = KuzuStore(str(tmp_path))
    store.store(MemoryItem(id='1', content='alpha', memory_type=MemoryType.
        WORKING, metadata={'tag': 'x'}))
    store.store(MemoryItem(id='2', content='beta', memory_type=MemoryType.
        WORKING, metadata={'tag': 'y'}))
    results = store.search({'metadata.tag': 'y'})
    assert len(results) == 1
    assert results[0].id == '2'
