import pytest

from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.application.memory.dto import MemoryRecord
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

    # Verify: results are normalized DTO records sourced from TinyDB
    assert len(results) >= 2
    assert all(isinstance(record, MemoryRecord) for record in results)
    assert {record.source for record in results} == {"tinydb"}
    assert all("alpha" in str(record.content).lower() for record in results)

    # Verify filtering by metadata and memory_type still works
    # Filter by memory_type=KNOWLEDGE should only include those metadata entries
    filtered = mm.search_memory(
        "alpha",
        memory_type=MemoryType.KNOWLEDGE,
        metadata_filter={"memory_type": MemoryType.KNOWLEDGE.value},
        limit=10,
    )
    assert len(filtered) >= 1
    assert all(isinstance(record, MemoryRecord) for record in filtered)
    assert all(
        record.metadata.get("memory_type") == MemoryType.KNOWLEDGE.value
        for record in filtered
    )
