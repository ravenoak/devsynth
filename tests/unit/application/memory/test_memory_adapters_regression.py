import tempfile
import pytest

from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


@pytest.mark.parametrize("adapter_cls", [TinyDBMemoryAdapter, GraphMemoryAdapter])
def test_store_retrieve_search_update(adapter_cls, tmp_path):
    if adapter_cls is GraphMemoryAdapter:
        adapter = adapter_cls(base_path=tmp_path)
    else:
        adapter = adapter_cls(db_path=str(tmp_path / "db.json"))

    item = MemoryItem(
        id="",
        content={"foo": "bar"},
        memory_type=MemoryType.KNOWLEDGE,
        metadata={"tag": "t"},
    )
    item_id = adapter.store(item)
    retrieved = adapter.retrieve(item_id)
    assert retrieved is not None
    assert retrieved.content["foo"] == "bar"

    results = adapter.search({"tag": "t"})
    assert any(r.id == item_id for r in results)

    item.content = {"foo": "baz"}
    adapter.store(item)
    updated = adapter.retrieve(item_id)
    assert updated.content["foo"] == "baz"


def test_vector_adapter_operations():
    adapter = VectorMemoryAdapter()
    vector = MemoryVector(
        id="", content="doc", embedding=[0.1, 0.2, 0.3], metadata={"kind": "test"}
    )
    vid = adapter.store_vector(vector)
    retrieved = adapter.retrieve_vector(vid)
    assert retrieved is not None
    assert retrieved.content == "doc"
    results = adapter.similarity_search([0.1, 0.2, 0.3], top_k=1)
    assert results and results[0].id == vid
