import pytest
from devsynth.application.memory.adapters.vector_memory_adapter import VectorMemoryAdapter
from devsynth.domain.models.memory import MemoryVector

@pytest.mark.medium
def test_similarity_empty_store():
    adapter = VectorMemoryAdapter()
    results = adapter.similarity_search([0.1, 0.2, 0.3])
    assert results == []

@pytest.mark.medium
def test_similarity_zero_norm(monkeypatch):
    adapter = VectorMemoryAdapter()
    vec = MemoryVector(id='v1', content='c', embedding=[0.0, 0.0], metadata=None)
    adapter.store_vector(vec)
    results = adapter.similarity_search([0.0, 0.0])
    assert results == [vec]

@pytest.mark.medium
def test_delete_missing():
    adapter = VectorMemoryAdapter()
    assert adapter.delete_vector('missing') is False

@pytest.mark.medium
def test_collection_stats():
    adapter = VectorMemoryAdapter()
    vec = MemoryVector(id='v1', content='c', embedding=[1.0, 0.0], metadata=None)
    adapter.store_vector(vec)
    stats = adapter.get_collection_stats()
    assert stats['vector_count'] == 1
    assert stats['embedding_dimensions'] == 2