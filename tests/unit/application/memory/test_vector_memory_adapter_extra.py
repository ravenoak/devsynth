import importlib
import sys

import pytest

from tests.fixtures.resources import (
    backend_import_reason,
    skip_if_missing_backend,
    skip_module_if_backend_disabled,
)

skip_module_if_backend_disabled("vector")
pytest.importorskip("numpy", reason=backend_import_reason("vector"))

pytestmark = skip_if_missing_backend("vector")

from devsynth.application.memory import vector_providers
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


@pytest.mark.fast
def test_default_provider_registration() -> None:
    """The vector provider factory registers the in-memory backend."""

    assert "in_memory" in vector_providers.factory.provider_types


@pytest.mark.fast
def test_optional_provider_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing optional imports skip registration without raising."""

    module_name = "devsynth.application.memory.vector_providers"
    original_import = importlib.import_module

    def fake_import(name: str, *args: object, **kwargs: object):
        if name == "devsynth.application.memory.adapters.vector_memory_adapter":
            raise ImportError("guarded")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    sys.modules.pop(module_name, None)
    guarded = importlib.import_module(module_name)
    try:
        assert "in_memory" not in guarded.factory.provider_types
    finally:
        sys.modules.pop(module_name, None)
        restored = importlib.import_module(module_name)
        globals()["vector_providers"] = restored
        assert "in_memory" in restored.factory.provider_types
