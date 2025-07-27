"""
Unit tests for ChromaDBMemoryStore.
"""

import os
import pytest
import tempfile
import shutil
import uuid
import time
from datetime import datetime
from unittest.mock import patch, MagicMock, create_autospec
from devsynth.adapters.chromadb_memory_store import (
    ChromaDBMemoryStore,
    _cleanup_chromadb_clients,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.provider_system import ProviderError

pytest.importorskip("chromadb")
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

pytestmark = pytest.mark.requires_resource("chromadb")


@pytest.fixture
def mock_chromadb_client():
    """Create a mock ChromaDB client for testing."""
    mock_client = create_autospec(ClientAPI)
    mock_collection = create_autospec(Collection)
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_client, mock_collection


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """Ensure all ChromaDB clients are cleaned up after tests."""
    yield
    _cleanup_chromadb_clients()


class TestChromaDBMemoryStore:
    """Tests for the ChromaDBMemoryStore class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self, request):
        """Create a unique temporary directory for each test."""
        test_name = request.node.name
        test_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp(prefix=f"chromadb_test_{test_name}_{test_id}_")
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        yield temp_dir
        time.sleep(0.5)
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Failed to clean up temp directory {temp_dir}: {e}")

    @pytest.fixture
    def collection_name(self, request):
        """Generate a unique collection name for each test."""
        return f"test_collection_{request.node.name}_{uuid.uuid4().hex}"

    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings for testing."""
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    @pytest.fixture
    def memory_store(self, temp_dir, collection_name, request, mock_chromadb_client):
        """Create a ChromaDBMemoryStore instance for testing with a mock ChromaDB client."""
        mock_client, mock_collection = mock_chromadb_client
        instance_id = f"test_{request.node.name}_{uuid.uuid4().hex}"

        class DummyEmbedder:

            def __call__(self, text):
                if isinstance(text, str):
                    return [0.1, 0.2, 0.3, 0.4, 0.5]
                return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in text]

        with (
            patch(
                "devsynth.adapters.chromadb_memory_store.chromadb_client_context"
            ) as mock_context,
            patch(
                "devsynth.adapters.chromadb_memory_store.embedding_functions.DefaultEmbeddingFunction",
                DummyEmbedder,
            ),
        ):
            mock_context.return_value.__enter__.return_value = mock_client
            store = ChromaDBMemoryStore(
                persist_directory=temp_dir,
                use_provider_system=False,
                collection_name=collection_name,
                max_retries=2,
                retry_delay=0.1,
                instance_id=instance_id,
            )
            store.collection = mock_collection
            yield store

    def test_initialization_with_default_embedder_has_expected(self, memory_store):
        """Test that ChromaDBMemoryStore initializes with default embedder when provider system is disabled.

        ReqID: N/A"""
        assert memory_store.use_provider_system is False
        assert hasattr(memory_store, "embedder")

    @patch("devsynth.adapters.chromadb_memory_store.embed")
    def test_initialization_with_provider_system_has_expected(
        self, mock_embed, temp_dir, collection_name, request, mock_chromadb_client
    ):
        """Test that ChromaDBMemoryStore initializes with provider system.

        ReqID: N/A"""
        mock_client, mock_collection = mock_chromadb_client
        mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]
        instance_id = f"test_provider_{request.node.name}_{uuid.uuid4().hex}"
        with patch(
            "devsynth.adapters.chromadb_memory_store.chromadb_client_context"
        ) as mock_context:
            mock_context.return_value.__enter__.return_value = mock_client
            store = ChromaDBMemoryStore(
                persist_directory=temp_dir,
                use_provider_system=True,
                collection_name=collection_name,
                max_retries=2,
                retry_delay=0.1,
                instance_id=instance_id,
            )
            store.collection = mock_collection
            assert store.use_provider_system is True
            embedding = store._get_embedding("test")
            mock_embed.assert_called_once_with(
                "test", provider_type=None, fallback=True
            )
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]

    @patch("devsynth.adapters.chromadb_memory_store.embed")
    def test_fallback_to_default_embedder_when_provider_fails(
        self, mock_embed, temp_dir, collection_name, request, mock_chromadb_client
    ):
        """Test that ChromaDBMemoryStore falls back to default embedder when provider system fails.

        ReqID: N/A"""
        mock_client, mock_collection = mock_chromadb_client
        mock_embed.side_effect = ProviderError("No valid providers available")
        instance_id = f"test_fallback_{request.node.name}_{uuid.uuid4().hex}"

        class DummyEmbedder:

            def __call__(self, text):
                if isinstance(text, str):
                    return [0.1, 0.2, 0.3, 0.4, 0.5]
                return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in text]

        with (
            patch(
                "devsynth.adapters.chromadb_memory_store.chromadb_client_context"
            ) as mock_context,
            patch(
                "devsynth.adapters.chromadb_memory_store.embedding_functions.DefaultEmbeddingFunction",
                DummyEmbedder,
            ),
        ):
            mock_context.return_value.__enter__.return_value = mock_client
            store = ChromaDBMemoryStore(
                persist_directory=temp_dir,
                use_provider_system=True,
                collection_name=collection_name,
                max_retries=2,
                retry_delay=0.1,
                instance_id=instance_id,
            )
            store.collection = mock_collection
            embedding = store._get_embedding("test")
            mock_embed.assert_called_once_with(
                "test", provider_type=None, fallback=True
            )
            assert embedding is not None

    def test_store_and_retrieve_succeeds(self, memory_store, mock_chromadb_client):
        """Test storing and retrieving items.

        ReqID: N/A"""
        _, mock_collection = mock_chromadb_client
        item = MemoryItem(
            id="test-item-1",
            content="This is a test item",
            memory_type=MemoryType.WORKING,
            metadata={"test": "value"},
        )
        mock_collection.get.return_value = {
            "ids": ["test-item-1"],
            "documents": ["This is a test item"],
            "metadatas": [
                {
                    "test": "value",
                    "memory_type": "working",
                    "created_at": datetime.now().isoformat(),
                }
            ],
        }
        item_id = memory_store.store(item)
        assert item_id == "test-item-1"
        mock_collection.add.assert_called_once()
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "This is a test item"
        assert retrieved_item.memory_type == MemoryType.WORKING
        assert retrieved_item.metadata.get("test") == "value"

    def test_search_succeeds(self, memory_store, mock_chromadb_client):
        """Test searching for items.

        ReqID: N/A"""
        _, mock_collection = mock_chromadb_client
        mock_collection.query.return_value = {
            "ids": [["item-1", "item-2"]],
            "documents": [
                ["This is the first test item", "This is the second test item"]
            ],
            "metadatas": [
                [
                    {
                        "index": 1,
                        "memory_type": "working",
                        "created_at": datetime.now().isoformat(),
                    },
                    {
                        "index": 2,
                        "memory_type": "working",
                        "created_at": datetime.now().isoformat(),
                    },
                ]
            ],
            "distances": [[0.1, 0.2]],
        }
        items = [
            MemoryItem(
                id="item-1",
                content="This is the first test item",
                memory_type=MemoryType.WORKING,
                metadata={"index": 1},
            ),
            MemoryItem(
                id="item-2",
                content="This is the second test item",
                memory_type=MemoryType.WORKING,
                metadata={"index": 2},
            ),
        ]
        results = memory_store.search({"query": "test item", "top_k": 2})
        mock_collection.query.assert_called_once()
        assert len(results) == 2
        result_ids = [item.id for item in results]
        assert "item-1" in result_ids
        assert "item-2" in result_ids

    def test_delete_succeeds(self, memory_store, mock_chromadb_client):
        """Test deleting items.

        ReqID: N/A"""
        _, mock_collection = mock_chromadb_client
        mock_collection.get.return_value = {
            "ids": ["delete-test-item"],
            "documents": ["This is an item to delete"],
            "metadatas": [
                {
                    "test": "delete",
                    "memory_type": "working",
                    "created_at": datetime.now().isoformat(),
                }
            ],
        }
        item = MemoryItem(
            id="delete-test-item",
            content="This is an item to delete",
            memory_type=MemoryType.WORKING,
            metadata={"test": "delete"},
        )
        item_id = memory_store.store(item)
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None
        result = memory_store.delete(item_id)
        mock_collection.delete.assert_called_once_with(ids=["delete-test-item"])
        assert result is True

        def get_side_effect(ids):
            if ids == ["delete-test-item"]:
                return {"ids": [], "documents": [], "metadatas": []}
            else:
                return {
                    "ids": ["delete-test-item"],
                    "documents": ["This is an item to delete"],
                    "metadatas": [
                        {
                            "test": "delete",
                            "memory_type": "working",
                            "created_at": datetime.now().isoformat(),
                        }
                    ],
                }

        mock_collection.get.side_effect = get_side_effect
        with pytest.raises(RuntimeError) as excinfo:
            memory_store.retrieve(item_id)
        assert "Item delete-test-item not found" in str(excinfo.value)

    def test_get_all_items_returns_items(self, memory_store, mock_chromadb_client):
        """Test that get_all_items returns stored items."""

        _, mock_collection = mock_chromadb_client
        now = datetime.now().isoformat()
        mock_collection.get.return_value = {
            "ids": ["a", "b"],
            "documents": ["A", "B"],
            "metadatas": [
                {"memory_type": "working", "created_at": now},
                {"memory_type": "working", "created_at": now},
            ],
        }

        items = memory_store.get_all_items()

        mock_collection.get.assert_called_once_with(include=["documents", "metadatas"])
        assert len(items) == 2
        assert {itm.id for itm in items} == {"a", "b"}
