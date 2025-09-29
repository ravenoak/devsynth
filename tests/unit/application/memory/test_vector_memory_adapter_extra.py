import pytest

import pytest

from devsynth.application.memory.adapters.vector_memory_adapter import (
    VectorMemoryAdapter,
)
from devsynth.application.memory.dto import MemoryRecord
from devsynth.domain.models.memory import MemoryType, MemoryVector


@pytest.mark.medium
def test_similarity_empty_store():
    adapter = VectorMemoryAdapter()
    results = adapter.similarity_search([0.1, 0.2, 0.3])
    assert isinstance(results, list)
    assert results == []


@pytest.mark.medium
def test_similarity_zero_norm(monkeypatch):
    adapter = VectorMemoryAdapter()
    vec = MemoryVector(id="v1", content="c", embedding=[0.0, 0.0], metadata=None)
    adapter.store_vector(vec)
    results = adapter.similarity_search([0.0, 0.0])
    assert isinstance(results, list)
    assert len(results) == 1
    record = results[0]
    assert isinstance(record, MemoryRecord)
    assert record.item.id == vec.id
    assert record.item.content == vec.content
    assert isinstance(record.metadata, dict)
    assert record.metadata.get("embedding") == vec.embedding
    assert record.metadata.get("memory_type") == MemoryType.CONTEXT.value


@pytest.mark.medium
def test_delete_missing():
    adapter = VectorMemoryAdapter()
    assert adapter.delete_vector("missing") is False


@pytest.mark.medium
def test_collection_stats():
    adapter = VectorMemoryAdapter()
    vec = MemoryVector(id="v1", content="c", embedding=[1.0, 0.0], metadata=None)
    adapter.store_vector(vec)
    stats = adapter.get_collection_stats()
    assert stats["vector_count"] == 1
    assert stats["embedding_dimensions"] == 2
