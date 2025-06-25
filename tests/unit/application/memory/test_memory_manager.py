import importlib.util
import pathlib
import types
from unittest.mock import MagicMock

import pytest

SRC_ROOT = pathlib.Path(__file__).resolve().parents[4] / "src"


def _load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Create minimal package so heavy optional deps are avoided
package_path = SRC_ROOT / "devsynth/application/memory"
dummy_pkg = types.ModuleType("devsynth.application.memory")
dummy_pkg.__path__ = [str(package_path)]
import sys

sys.modules.setdefault("devsynth.application.memory", dummy_pkg)

memory_manager_module = _load_module(
    package_path / "memory_manager.py", "devsynth.application.memory.memory_manager"
)

MemoryManager = memory_manager_module.MemoryManager
from devsynth.domain.models.memory import MemoryType


class DummyVectorStore:
    def __init__(self):
        self.stored = []

    def store(self, item):
        self.stored.append(item)
        return "vector-id"


class TestMemoryManagerStore:
    @pytest.fixture
    def adapters(self):
        tinydb = MagicMock()
        vector = DummyVectorStore()
        return {"tinydb": tinydb, "vector": vector}

    def test_store_prefers_tinydb(self, adapters):
        manager = MemoryManager(adapters=adapters)
        manager.store_with_edrr_phase("x", MemoryType.CODE, "EXPAND")
        adapters["tinydb"].store.assert_called_once()
        assert not adapters["vector"].stored

    def test_store_falls_back_to_first(self):
        vector = DummyVectorStore()
        manager = MemoryManager(adapters={"vector": vector})
        manager.store_with_edrr_phase("x", MemoryType.CODE, "EXPAND")
        assert vector.stored


class TestEmbedText:
    def test_fallback_and_provider(self):
        manager = MemoryManager()
        default = manager._embed_text("abc", dimension=5)

        provider = MagicMock()
        provider.embed.side_effect = Exception("boom")
        manager_fail = MemoryManager(embedding_provider=provider)
        assert manager_fail._embed_text("abc", dimension=5) == default

        provider.embed.side_effect = None
        provider.embed.return_value = [1.0, 2.0]
        manager_ok = MemoryManager(embedding_provider=provider)
        assert manager_ok._embed_text("hi") == [1.0, 2.0]
