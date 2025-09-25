"""Tests for documentation ingestion search variance handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from devsynth.application.documentation.ingestion import DocumentationIngestionManager
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector


@pytest.fixture
def mock_memory_manager() -> MagicMock:
    """Create a mock memory manager for search tests."""

    manager = MagicMock()
    manager.search_memory.return_value = []
    manager.query_by_metadata.return_value = []
    return manager


@pytest.mark.fast
def test_search_documentation_prefers_vector_results(
    mock_memory_manager: MagicMock,
) -> None:
    """Vector search results are materialised verbatim.

    ReqID: N/A
    """

    vector = MemoryVector(
        id="vector-1",
        content="vector content",
        embedding=[0.1, 0.2, 0.3],
        metadata={"type": MemoryType.DOCUMENTATION.value},
    )
    mock_memory_manager.search_memory.return_value = [vector]

    manager = DocumentationIngestionManager(memory_manager=mock_memory_manager)

    results = manager.search_documentation("query")

    assert isinstance(results, tuple)
    assert results == (vector,)
    assert all(isinstance(item, MemoryVector) for item in results)
    mock_memory_manager.query_by_metadata.assert_not_called()


@pytest.mark.fast
def test_search_documentation_falls_back_to_metadata_items(
    mock_memory_manager: MagicMock,
) -> None:
    """Metadata search results are returned when vectors are unavailable.

    ReqID: N/A
    """

    mock_memory_manager.search_memory.return_value = []
    item = MemoryItem(
        id="item-1",
        content="item content",
        memory_type=MemoryType.DOCUMENTATION,
        metadata={},
    )
    mock_memory_manager.query_by_metadata.return_value = [item]

    manager = DocumentationIngestionManager(memory_manager=mock_memory_manager)

    metadata_filter = {"region": "docs"}
    results = manager.search_documentation("query", metadata_filter=metadata_filter)

    assert isinstance(results, tuple)
    assert results == (item,)
    assert all(isinstance(materialised, MemoryItem) for materialised in results)

    mock_memory_manager.search_memory.assert_called_once()
    mock_memory_manager.query_by_metadata.assert_called_once()
    fallback_filter = mock_memory_manager.query_by_metadata.call_args[0][0]
    assert fallback_filter["type"] == MemoryType.DOCUMENTATION.value
    assert fallback_filter["region"] == "docs"
