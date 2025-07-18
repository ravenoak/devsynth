import pytest
from datetime import datetime
from devsynth.domain.models.memory import MemoryType, MemoryItem, MemoryItemType


class TestMemoryModels:
    """Tests for the MemoryModels component.

ReqID: N/A"""

    def test_memory_type_enum_succeeds(self):
        """Test that memory type enum succeeds.

ReqID: N/A"""
        assert MemoryType.SHORT_TERM.value == 'short_term'
        assert MemoryType.LONG_TERM.value == 'long_term'
        assert MemoryType.WORKING.value == 'working'
        assert MemoryType.EPISODIC.value == 'episodic'

    def test_memory_item_initialization_succeeds(self):
        """Test that memory item initialization succeeds.

ReqID: N/A"""
        memory_item = MemoryItem(id='test-memory-1', content=
            'Test memory content', memory_type=MemoryType.SHORT_TERM)
        assert memory_item.id == 'test-memory-1'
        assert memory_item.content == 'Test memory content'
        assert memory_item.memory_type == MemoryType.SHORT_TERM
        assert isinstance(memory_item.metadata, dict)
        assert isinstance(memory_item.created_at, datetime)

    def test_memory_item_with_metadata_succeeds(self):
        """Test that memory item with metadata succeeds.

ReqID: N/A"""
        custom_time = datetime.now()
        custom_metadata = {'source': 'user_input', 'priority': 'high',
            'tags': ['requirement', 'feature']}
        memory_item = MemoryItem(id='test-memory-2', content={'key':
            'structured content'}, memory_type=MemoryType.LONG_TERM,
            metadata=custom_metadata, created_at=custom_time)
        assert memory_item.id == 'test-memory-2'
        assert memory_item.content == {'key': 'structured content'}
        assert memory_item.memory_type == MemoryType.LONG_TERM
        assert memory_item.metadata == custom_metadata
        assert memory_item.created_at == custom_time

    def test_memory_type_aliases(self):
        """Ensure enum aliases reference the same member."""

        # WORKING_MEMORY should refer to the same enum member as WORKING
        assert MemoryType.WORKING_MEMORY is MemoryType.WORKING

    def test_memory_item_type_alias(self):
        """Ensure MemoryItemType is an alias of MemoryType."""

        assert MemoryItemType is MemoryType
        # Spot check a member via the alias
        assert MemoryItemType.SHORT_TERM is MemoryType.SHORT_TERM
