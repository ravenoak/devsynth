import pytest
import os
import tempfile
import shutil
from devsynth.application.memory.kuzu_store import KuzuStore
from devsynth.domain.models.memory import MemoryItem, MemoryType

@pytest.mark.medium
def test_init_creates_directory(tmp_path):
    path = tmp_path / 'store'
    store = KuzuStore(str(path))
    try:
        assert path.exists()
        assert store.file_path == str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)

@pytest.mark.medium
def test_store_and_retrieve_succeeds(tmp_path):
    store = KuzuStore(str(tmp_path))
    item = MemoryItem(id='a', content='hello', memory_type=MemoryType.WORKING)
    store.store(item)
    got = store.retrieve('a')
    assert got is not None
    assert got.content == 'hello'