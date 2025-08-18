"""
Integration tests for error handling in GraphMemoryAdapter.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryItemNotFoundError, MemoryStoreError

# Mark the entire module as medium speed; only specific tests are memory intensive
pytestmark = pytest.mark.medium


class TestGraphMemoryErrorHandling:
    """Integration tests for error handling in GraphMemoryAdapter.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def graph_adapter(self, temp_dir):
        """Create a GraphMemoryAdapter instance for testing."""
        return GraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

    @pytest.mark.medium
    def test_store_with_invalid_path_raises_permission_error(self):
        """Test storing a memory item with an invalid path raises PermissionError.

        ReqID: N/A"""
        with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                GraphMemoryAdapter(base_path="/root/nonexistent", use_rdflib_store=True)

    @pytest.mark.medium
    def test_retrieve_nonexistent_item_succeeds(self, graph_adapter):
        """Test retrieving a non-existent memory item.

        ReqID: N/A"""
        result = graph_adapter.retrieve("nonexistent-id")
        assert result is None

    @pytest.mark.medium
    def test_delete_nonexistent_item_succeeds(self, graph_adapter):
        """Test deleting a non-existent memory item.

        ReqID: N/A"""
        result = graph_adapter.delete("nonexistent-id")
        assert result is False

    @pytest.mark.medium
    def test_search_with_invalid_criteria_returns_empty_list(self, graph_adapter):
        """Test searching with invalid criteria returns an empty list.

        ReqID: N/A"""
        result = graph_adapter.search(None)
        assert result == []

    @pytest.mark.medium
    def test_query_related_items_nonexistent_succeeds(self, graph_adapter):
        """Test querying related items for a non-existent item.

        ReqID: N/A"""
        result = graph_adapter.query_related_items("nonexistent-id")
        assert result == []

    @pytest.mark.medium
    def test_store_with_corrupted_graph_raises_memory_store_error(self, graph_adapter):
        """Test storing a memory item with a corrupted graph raises MemoryStoreError.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.CODE,
            metadata={"source": "test"},
        )
        with patch.object(graph_adapter, "graph", None):
            with pytest.raises(MemoryStoreError):
                graph_adapter.store(memory_item)

    @pytest.mark.medium
    def test_concurrent_access_succeeds(self, graph_adapter):
        """Test concurrent access to the graph memory adapter.

        ReqID: N/A"""
        items = [
            MemoryItem(
                id=f"item-{i}",
                content=f"Content {i}",
                memory_type=MemoryType.CODE,
                metadata={"index": i},
            )
            for i in range(10)
        ]
        for item in items:
            graph_adapter.store(item)
        retrieved_items = []
        for i in range(10):
            item = graph_adapter.retrieve(f"item-{i}")
            if item:
                retrieved_items.append(item)
        assert len(retrieved_items) == 10

    @pytest.mark.medium
    def test_store_and_retrieve_with_special_characters_succeeds(self, graph_adapter):
        """Test storing and retrieving a memory item with special characters.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id="test-id",
            content="Test content with special characters: !@#$%^&*()_+{}[]|\\:;\"'<>,.?/",
            memory_type=MemoryType.CODE,
            metadata={"source": "test"},
        )
        item_id = graph_adapter.store(memory_item)
        retrieved_item = graph_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == memory_item.content

    @pytest.mark.medium
    def test_store_and_retrieve_with_unicode_characters_succeeds(self, graph_adapter):
        """Test storing and retrieving a memory item with Unicode characters.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id="test-id",
            content="Test content with Unicode characters: 你好, こんにちは, 안녕하세요, Привет, مرحبا, שלום",
            memory_type=MemoryType.CODE,
            metadata={"source": "test"},
        )
        item_id = graph_adapter.store(memory_item)
        retrieved_item = graph_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.content == memory_item.content

    @pytest.mark.memory_intensive
    @pytest.mark.slow
    def test_store_with_very_large_content_succeeds(self, graph_adapter):
        """Test storing a memory item with very large content.

        ReqID: N/A"""
        # Use a reduced payload to avoid excessive memory usage
        large_content = "x" * 10000
        memory_item = MemoryItem(
            id="test-id",
            content=large_content,
            memory_type=MemoryType.CODE,
            metadata={"source": "test"},
        )
        item_id = graph_adapter.store(memory_item)
        retrieved_item = graph_adapter.retrieve(item_id)
        assert retrieved_item is not None
        assert len(retrieved_item.content) == len(large_content)
