import importlib.util
import pathlib
import sys
import types
from typing import Union

import pytest

from devsynth.application.memory.dto import MemoryRecord
from devsynth.domain.models.memory import MemoryType, MemoryVector

SRC_ROOT = pathlib.Path(__file__).resolve().parents[4] / "src"


def _load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PACKAGE_PATH = SRC_ROOT / "devsynth/application/memory"
memory_manager_module = _load_module(
    PACKAGE_PATH / "memory_manager.py", "devsynth.application.memory.memory_manager"
)
vector_adapter_module = _load_module(
    PACKAGE_PATH / "adapters/vector_memory_adapter.py",
    "devsynth.application.memory.adapters.vector_memory_adapter",
)
MemoryManager = memory_manager_module.MemoryManager
VectorMemoryAdapter = vector_adapter_module.VectorMemoryAdapter


@pytest.fixture(autouse=True)
def _patch_memory_module(monkeypatch):
    pkg = types.ModuleType("devsynth.application.memory")
    pkg.__path__ = [str(PACKAGE_PATH)]
    monkeypatch.setitem(sys.modules, "devsynth.application.memory", pkg)


class TestMemoryManagerSearch:
    """Tests for the MemoryManagerSearch component.

    ReqID: N/A"""

    @pytest.fixture
    def manager(self):
        adapter = VectorMemoryAdapter()
        return MemoryManager(adapters={"vector": adapter})

    def _add_vector(
        self,
        manager: MemoryManager,
        text: str,
        memory_type: MemoryType | str,
        **metadata,
    ):
        embedding = manager._embed_text(text)
        meta = {
            "memory_type": (
                memory_type.value if hasattr(memory_type, "value") else memory_type
            )
        }
        meta.update(metadata)
        vector = MemoryVector(id="", content=text, embedding=embedding, metadata=meta)
        manager.adapters["vector"].store_vector(vector)
        return vector

    @pytest.mark.medium
    def test_search_returns_similar_results_succeeds(self, manager):
        """Test that search returns similar results succeeds.

        ReqID: N/A"""
        self._add_vector(manager, "apple item", MemoryType.CODE)
        self._add_vector(manager, "banana item", MemoryType.CODE)
        self._add_vector(manager, "car", "DOC")
        results = manager.search_memory("apple", limit=2)
        assert results
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert results[0].content == "apple item"

    @pytest.mark.medium
    def test_search_filters_by_metadata_succeeds(self, manager):
        """Test that search filters by metadata succeeds.

        ReqID: N/A"""
        self._add_vector(manager, "apple item", MemoryType.CODE, category="fruit")
        self._add_vector(manager, "banana item", MemoryType.CODE, category="fruit")
        self._add_vector(manager, "car", "DOC", category="vehicle")
        results = manager.search_memory(
            "apple",
            memory_type=MemoryType.CODE,
            metadata_filter={"category": "fruit"},
            limit=5,
        )
        assert len(results) == 2
        assert all(isinstance(record, MemoryRecord) for record in results)
        assert all(record.metadata.get("category") == "fruit" for record in results)
