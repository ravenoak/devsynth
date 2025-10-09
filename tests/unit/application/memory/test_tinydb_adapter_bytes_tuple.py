import os
from datetime import datetime

import pytest

from devsynth.application.memory.adapters.tinydb_memory_adapter import (
    TinyDBMemoryAdapter,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType

pytestmark = pytest.mark.requires_resource("tinydb")


@pytest.mark.fast
def test_tinydb_adapter_serializes_bytes_and_tuple(tmp_path):
    """Ensure TinyDBMemoryAdapter serializes non-JSON types safely.

    This guards against the TypeError observed during `task release:prep` when
    metadata/content contain bytes or tuples.
    """
    adapter = TinyDBMemoryAdapter(db_path=str(tmp_path / "db.json"))

    item = MemoryItem(
        id="bytes_tuple",
        content={
            "payload": b"hello",
            "coords": (1, 2, 3),
            "nested": {"t": ("a", "b")},
        },
        memory_type=MemoryType.KNOWLEDGE,
        metadata={
            "tags": ("x", "y"),
            "raw": b"world",
            "timestamp": datetime(2024, 1, 1),
        },
    )

    stored_id = adapter.store(item)
    assert stored_id == item.id

    retrieved = adapter.retrieve(stored_id)
    assert retrieved is not None

    # bytes should become a string representation (utf-8 or base64); at least be str
    assert isinstance(retrieved.content["payload"], str)
    assert isinstance(retrieved.metadata["raw"], str)

    # tuples should become lists
    assert retrieved.content["coords"] == [1, 2, 3]
    assert retrieved.content["nested"]["t"] == ["a", "b"]
    assert retrieved.metadata["tags"] == ["x", "y"]

    # datetime should round-trip as ISO string (already covered elsewhere but asserted here for completeness)
    assert isinstance(retrieved.metadata["timestamp"], str)

    # Serialization should persist the enum value and tolerate legacy uppercase forms
    serialized = adapter._memory_item_to_dict(item)
    assert serialized["memory_type"] == MemoryType.KNOWLEDGE.value
    legacy_serialized = dict(serialized)
    legacy_serialized["memory_type"] = MemoryType.KNOWLEDGE.name
    restored = adapter._dict_to_memory_item(legacy_serialized)
    assert restored.memory_type is MemoryType.KNOWLEDGE
