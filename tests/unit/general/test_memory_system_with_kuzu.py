import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.domain.models.memory import MemoryItem, MemoryType, MemoryVector

pytest.importorskip("kuzu")

# Memory system tests involve kuzu but remain reasonably quick

pytestmark = [pytest.mark.requires_resource("kuzu")]


class TestMemorySystemWithKuzu:
    """Tests for the MemorySystemWithKuzu component.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture(autouse=True)
    def mock_embed(self):
        with patch(
            "devsynth.adapters.kuzu_memory_store.embed", return_value=[[0.1, 0.2, 0.3]]
        ):
            yield

    @pytest.fixture
    def memory_system(self, temp_dir):
        config = {
            "memory_store_type": "kuzu",
            "memory_file_path": temp_dir,
            "vector_store_enabled": True,
        }
        return MemorySystemAdapter(config=config)

    @pytest.mark.medium
    def test_initialization_with_kuzu_succeeds(self, temp_dir):
        """Test that initialization with kuzu succeeds.

        ReqID: N/A"""
        config = {
            "memory_store_type": "kuzu",
            "memory_file_path": temp_dir,
            "vector_store_enabled": True,
        }
        memory_system = MemorySystemAdapter(config=config)
        assert memory_system.memory_store is not None
        assert memory_system.vector_store is not None
        assert isinstance(memory_system.vector_store, KuzuAdapter)
        assert memory_system.has_vector_store() is True

    @pytest.mark.medium
    def test_memory_and_vector_store_integration_succeeds(self, memory_system):
        """Test that memory and vector store integration succeeds.

        ReqID: N/A"""
        memory_item = MemoryItem(
            id="test-item",
            content="This is a test item",
            memory_type=MemoryType.LONG_TERM,
            metadata={"test": "memory"},
        )
        memory_store = memory_system.get_memory_store()
        item_id = memory_store.store(memory_item)
        vector = MemoryVector(
            id="test-vector",
            content="This is a test vector",
            embedding=[0.1, 0.2, 0.3],
            metadata={"memory_item_id": item_id},
        )
        vector_store = memory_system.get_vector_store()
        vector_id = vector_store.store_vector(vector)
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None
        retrieved_vector = vector_store.retrieve_vector(vector_id)
        assert retrieved_vector is not None
        assert retrieved_vector.metadata["memory_item_id"] == item_id
