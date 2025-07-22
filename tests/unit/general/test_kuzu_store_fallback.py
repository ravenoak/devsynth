import importlib
import sys
from pathlib import Path
import tempfile
import shutil
from devsynth.domain.models.memory import MemoryItem, MemoryType


def test_kuzu_store_falls_back_when_dependency_missing(monkeypatch):
    # Remove kuzu module to simulate missing dependency
    monkeypatch.setitem(sys.modules, "kuzu", None)
    # Reload module after patching
    spec = importlib.util.spec_from_file_location(
        "kuzu_store", Path(__file__).resolve().parents[3] / "src/devsynth/application/memory/kuzu_store.py"
    )
    kuzu_store = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kuzu_store)
    KuzuStore = kuzu_store.KuzuStore

    temp_dir = tempfile.mkdtemp()
    try:
        store = KuzuStore(temp_dir)
        assert store._use_fallback is True
        item = MemoryItem(id="a", content="hello", memory_type=MemoryType.WORKING)
        store.store(item)
        retrieved = store.retrieve("a")
        assert retrieved is not None
        assert retrieved.content == "hello"
    finally:
        shutil.rmtree(temp_dir)

