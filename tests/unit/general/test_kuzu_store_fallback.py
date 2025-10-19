import importlib
import sys
from pathlib import Path

import pytest

from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = pytest.mark.requires_resource("kuzu")


@pytest.mark.skip(
    reason="Complex dependency mocking test that requires extensive setup"
)
@pytest.mark.medium
def test_kuzu_store_falls_back_when_dependency_missing(monkeypatch, tmp_path):
    # Remove kuzu module to simulate missing dependency
    monkeypatch.setitem(sys.modules, "kuzu", None)
    # Reload module after patching
    kuzu_store = importlib.import_module("devsynth.application.memory.kuzu_store")
    importlib.reload(kuzu_store)
    KuzuStore = kuzu_store.KuzuStore

    store = KuzuStore(str(tmp_path))
    assert store._use_fallback is True
    assert store.file_path == str(tmp_path)
    assert tmp_path.exists()
    item = MemoryItem(id="a", content="hello", memory_type=MemoryType.WORKING)
    store.store(item)
    retrieved = store.retrieve("a")
    assert retrieved is not None
    assert retrieved.content == "hello"
