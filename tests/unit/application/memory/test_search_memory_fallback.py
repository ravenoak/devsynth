import pytest

from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryItem, MemoryType


@pytest.mark.no_network
@pytest.mark.fast
def test_search_memory_fallback_without_vector_adapter_returns_results():
    # Setup MemoryManager with only TinyDB (no vector adapter)
    mm = MemoryManager(adapters={"tinydb": TinyDBMemoryAdapter()})

    # Store some items
    items = [
        MemoryItem(
            id="",
            content="Alpha beta gamma",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"memory_type": MemoryType.KNOWLEDGE.value},
        ),
        MemoryItem(
            id="",
            content="Delta epsilon zeta",
            memory_type=MemoryType.DOCUMENTATION,
            metadata={"memory_type": MemoryType.DOCUMENTATION.value},
        ),
        MemoryItem(
            id="",
            content="Gamma delta alpha",
            memory_type=MemoryType.KNOWLEDGE,
            metadata={"memory_type": MemoryType.KNOWLEDGE.value},
        ),
    ]

    for it in items:
        mm.store_item(it)

    # Execute: query that matches two items by keyword
    results = mm.search_memory("alpha", limit=10)

    # Verify: should not be empty and embeddings should be optional (empty list)
    assert len(results) >= 2
    assert all(hasattr(v, "embedding") for v in results)
    # Ensure that we are not requiring real embeddings
    assert all(v.embedding == [] for v in results)

    # Verify filtering by metadata and memory_type still works
    # Filter by memory_type=KNOWLEDGE should only include those metadata entries
    filtered = mm.search_memory(
        "alpha",
        memory_type=MemoryType.KNOWLEDGE,
        metadata_filter={"memory_type": MemoryType.KNOWLEDGE.value},
        limit=10,
    )
    assert len(filtered) >= 1
    assert all(
        v.metadata.get("memory_type") == MemoryType.KNOWLEDGE.value for v in filtered
    )
