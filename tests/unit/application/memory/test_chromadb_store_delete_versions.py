"""Tests that delete() cleans up versions in ChromaDB.

This covers Task 11 sub-item: Harden ChromaDB adapter transactions and error handling
by ensuring versioned documents are also removed when an item is deleted.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

pytest.importorskip("chromadb")
pytest.importorskip("tiktoken")

from devsynth.application.memory.chromadb_store import ChromaDBStore
from devsynth.domain.models.memory import MemoryItem


@pytest.mark.medium
@pytest.mark.requires_resource("chromadb")
def test_delete_also_removes_versions(tmp_path):
    # Arrange: create store in a mode where we can inject mocks
    store = ChromaDBStore(str(tmp_path))

    # Inject mocks for collections
    store._use_fallback = False
    store.collection = MagicMock()
    store.versions_collection = MagicMock()

    # Stub retrieve to return a MemoryItem to allow deletion to proceed
    item = MemoryItem(
        id="abc", content="x", memory_type=None, metadata={}, created_at=None
    )
    store.retrieve = lambda item_id: item if item_id == "abc" else None  # type: ignore

    # Act
    ok = store.delete("abc")

    # Assert
    assert ok is True
    store.collection.delete.assert_called_once_with(ids=["abc"])  # type: ignore[attr-defined]
    # Versions collection should be cleaned using a where-filter
    store.versions_collection.delete.assert_called_once()  # type: ignore[attr-defined]
    kwargs = store.versions_collection.delete.call_args.kwargs  # type: ignore[attr-defined]
    assert kwargs.get("where") == {"original_id": "abc"}
