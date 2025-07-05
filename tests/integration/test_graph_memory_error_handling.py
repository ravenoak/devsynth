"""
Integration tests for error handling in GraphMemoryAdapter.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from devsynth.application.memory.adapters.graph_memory_adapter import GraphMemoryAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import MemoryStoreError, MemoryItemNotFoundError


class TestGraphMemoryErrorHandling:
    """Integration tests for error handling in GraphMemoryAdapter."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def graph_adapter(self, temp_dir):
        """Create a GraphMemoryAdapter instance for testing."""
        return GraphMemoryAdapter(base_path=temp_dir, use_rdflib_store=True)

    def test_store_with_invalid_path(self):
        """Test storing a memory item with an invalid path."""
        # Create an adapter with a non-existent path that can't be created
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            with pytest.raises(MemoryStoreError):
                GraphMemoryAdapter(base_path="/root/nonexistent", use_rdflib_store=True)

    def test_retrieve_nonexistent_item(self, graph_adapter):
        """Test retrieving a non-existent memory item."""
        # Attempt to retrieve a non-existent item
        result = graph_adapter.retrieve("nonexistent-id")
        assert result is None

    def test_delete_nonexistent_item(self, graph_adapter):
        """Test deleting a non-existent memory item."""
        # Attempt to delete a non-existent item
        result = graph_adapter.delete("nonexistent-id")
        assert result is False

    def test_search_with_invalid_criteria(self, graph_adapter):
        """Test searching with invalid criteria."""
        # Search with invalid criteria (None)
        with pytest.raises(TypeError):
            graph_adapter.search(None)

    def test_query_related_items_nonexistent(self, graph_adapter):
        """Test querying related items for a non-existent item."""
        # Query related items for a non-existent item
        result = graph_adapter.query_related_items("nonexistent-id")
        assert result == []

    def test_store_with_corrupted_graph(self, graph_adapter):
        """Test storing a memory item with a corrupted graph."""
        # Create a memory item
        memory_item = MemoryItem(
            id="test-id",
            content="Test content",
            memory_type=MemoryType.CODE,
            metadata={"source": "test"}
        )

        # Corrupt the graph by setting it to None
        with patch.object(graph_adapter, 'graph', None):
            with pytest.raises(AttributeError):
                graph_adapter.store(memory_item)

    def test_concurrent_access(self, graph_adapter):
        """Test concurrent access to the graph memory adapter."""
        # Create memory items
        items = [
            MemoryItem(
                id=f"item-{i}",
                content=f"Content {i}",
                memory_type=MemoryType.CODE,
                metadata={"index": i}
            )
            for i in range(10)
        ]

        # Store items concurrently (simulated with a loop)
        for item in items:
            graph_adapter.store(item)

        # Retrieve items concurrently (simulated with a loop)
        retrieved_items = []
        for i in range(10):
            item = graph_adapter.retrieve(f"item-{i}")
            if item:
                retrieved_items.append(item)

        # Check that all items were retrieved
        assert len(retrieved_items) == 10

    def test_store_and_retrieve_with_special_characters(self, graph_adapter):
        """Test storing and retrieving a memory item with special characters."""
        # Create a memory item with special characters
        memory_item = MemoryItem(
            id="test-id",
            content="Test content with special characters: !@#$%^&*()_+{}[]|\\:;\"'<>,.?/",
            memory_type=MemoryType.CODE,
            metadata={"source": "test"}
        )

        # Store the item
        item_id = graph_adapter.store(memory_item)

        # Retrieve the item
        retrieved_item = graph_adapter.retrieve(item_id)

        # Check that the item was retrieved correctly
        assert retrieved_item is not None
        assert retrieved_item.content == memory_item.content

    def test_store_and_retrieve_with_unicode_characters(self, graph_adapter):
        """Test storing and retrieving a memory item with Unicode characters."""
        # Create a memory item with Unicode characters
        memory_item = MemoryItem(
            id="test-id",
            content="Test content with Unicode characters: 你好, こんにちは, 안녕하세요, Привет, مرحبا, שלום",
            memory_type=MemoryType.CODE,
            metadata={"source": "test"}
        )

        # Store the item
        item_id = graph_adapter.store(memory_item)

        # Retrieve the item
        retrieved_item = graph_adapter.retrieve(item_id)

        # Check that the item was retrieved correctly
        assert retrieved_item is not None
        assert retrieved_item.content == memory_item.content

    def test_store_with_very_large_content(self, graph_adapter):
        """Test storing a memory item with very large content."""
        # Create a memory item with very large content
        large_content = "x" * 1000000  # 1MB of content
        memory_item = MemoryItem(
            id="test-id",
            content=large_content,
            memory_type=MemoryType.CODE,
            metadata={"source": "test"}
        )

        # Store the item
        item_id = graph_adapter.store(memory_item)

        # Retrieve the item
        retrieved_item = graph_adapter.retrieve(item_id)

        # Check that the item was retrieved correctly
        assert retrieved_item is not None
        assert len(retrieved_item.content) == len(large_content)