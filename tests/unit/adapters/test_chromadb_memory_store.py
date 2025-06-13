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

from devsynth.adapters.chromadb_memory_store import ChromaDBMemoryStore, _cleanup_chromadb_clients
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.adapters.provider_system import ProviderError

# Import ChromaDB dependencies
try:
    import chromadb
    from chromadb.api import ClientAPI
    from chromadb.api.models.Collection import Collection
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None
    ClientAPI = Collection = object

pytestmark = pytest.mark.requires_resource("chromadb")

# Create a mock ChromaDB client and collection for testing
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
    # Setup - nothing to do
    yield
    # Teardown - clean up all ChromaDB clients
    _cleanup_chromadb_clients()


class TestChromaDBMemoryStore:
    """Tests for the ChromaDBMemoryStore class."""

    @pytest.fixture
    def temp_dir(self, request):
        """Create a unique temporary directory for each test."""
        # Create a unique directory for each test to avoid ChromaDB client conflicts
        test_name = request.node.name
        test_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp(prefix=f"chromadb_test_{test_name}_{test_id}_")

        # Ensure the directory is empty
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        yield temp_dir

        # Wait a moment before cleanup to ensure ChromaDB has released resources
        time.sleep(0.5)

        # Clean up after the test
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Failed to clean up temp directory {temp_dir}: {e}")

    @pytest.fixture
    def collection_name(self, request):
        """Generate a unique collection name for each test."""
        # Use UUID to ensure uniqueness across test runs
        return f"test_collection_{request.node.name}_{uuid.uuid4().hex}"

    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings for testing."""
        return [0.1, 0.2, 0.3, 0.4, 0.5]

    @pytest.fixture
    def memory_store(self, temp_dir, collection_name, request, mock_chromadb_client):
        """Create a ChromaDBMemoryStore instance for testing with a mock ChromaDB client."""
        mock_client, mock_collection = mock_chromadb_client

        # Create a unique instance ID for this test
        instance_id = f"test_{request.node.name}_{uuid.uuid4().hex}"

        # Patch the chromadb client context and the default embedding function to avoid network calls
        class DummyEmbedder:
            def __call__(self, text):
                if isinstance(text, str):
                    return [0.1, 0.2, 0.3, 0.4, 0.5]
                return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in text]

        with patch('devsynth.adapters.chromadb_memory_store.chromadb_client_context') as mock_context, \
             patch('devsynth.adapters.chromadb_memory_store.embedding_functions.DefaultEmbeddingFunction', DummyEmbedder):
            # Configure the mock context manager to yield our mock client
            mock_context.return_value.__enter__.return_value = mock_client

            # Create the store with retry capabilities and a unique instance ID
            store = ChromaDBMemoryStore(
                persist_directory=temp_dir,
                use_provider_system=False,  # Don't use provider system for tests
                collection_name=collection_name,
                max_retries=2,
                retry_delay=0.1,
                instance_id=instance_id
            )

            # Set the collection directly to our mock collection
            store.collection = mock_collection

            yield store

            # No need to clean up as we're using mocks

    def test_initialization_with_default_embedder(self, memory_store):
        """Test that ChromaDBMemoryStore initializes with default embedder when provider system is disabled."""
        assert memory_store.use_provider_system is False
        assert hasattr(memory_store, 'embedder')

    @patch('devsynth.adapters.chromadb_memory_store.embed')
    def test_initialization_with_provider_system(self, mock_embed, temp_dir, collection_name, request, mock_chromadb_client):
        """Test that ChromaDBMemoryStore initializes with provider system."""
        mock_client, mock_collection = mock_chromadb_client

        # Mock the embed function to return a valid embedding
        mock_embed.return_value = [[0.1, 0.2, 0.3, 0.4, 0.5]]

        # Create a unique instance ID for this test
        instance_id = f"test_provider_{request.node.name}_{uuid.uuid4().hex}"

        # Patch the chromadb_client_context to return our mock client
        with patch('devsynth.adapters.chromadb_memory_store.chromadb_client_context') as mock_context:
            # Configure the mock context manager to yield our mock client
            mock_context.return_value.__enter__.return_value = mock_client

            # Create a store with provider system enabled
            store = ChromaDBMemoryStore(
                persist_directory=temp_dir,
                use_provider_system=True,
                collection_name=collection_name,
                max_retries=2,
                retry_delay=0.1,
                instance_id=instance_id
            )

            # Set the collection directly to our mock collection
            store.collection = mock_collection

            assert store.use_provider_system is True

            # Test that _get_embedding uses the provider system
            embedding = store._get_embedding("test")
            mock_embed.assert_called_once_with("test", provider_type=None, fallback=True)
            assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]

    @patch('devsynth.adapters.chromadb_memory_store.embed')
    def test_fallback_to_default_embedder_when_provider_fails(self, mock_embed, temp_dir, collection_name, request, mock_chromadb_client):
        """Test that ChromaDBMemoryStore falls back to default embedder when provider system fails."""
        mock_client, mock_collection = mock_chromadb_client

        # Mock the embed function to raise an error
        mock_embed.side_effect = ProviderError("No valid providers available")

        # Create a unique instance ID for this test
        instance_id = f"test_fallback_{request.node.name}_{uuid.uuid4().hex}"

        class DummyEmbedder:
            def __call__(self, text):
                if isinstance(text, str):
                    return [0.1, 0.2, 0.3, 0.4, 0.5]
                return [[0.1, 0.2, 0.3, 0.4, 0.5] for _ in text]

        # Patch the chromadb_client_context to return our mock client and the default embedder
        with patch('devsynth.adapters.chromadb_memory_store.chromadb_client_context') as mock_context, \
             patch('devsynth.adapters.chromadb_memory_store.embedding_functions.DefaultEmbeddingFunction', DummyEmbedder):
            # Configure the mock context manager to yield our mock client
            mock_context.return_value.__enter__.return_value = mock_client

            # Create a store with provider system enabled
            store = ChromaDBMemoryStore(
                persist_directory=temp_dir,
                use_provider_system=True,
                collection_name=collection_name,
                max_retries=2,
                retry_delay=0.1,
                instance_id=instance_id
            )

            # Set the collection directly to our mock collection
            store.collection = mock_collection

            # Test that _get_embedding falls back to default embedder
            embedding = store._get_embedding("test")
            mock_embed.assert_called_once_with("test", provider_type=None, fallback=True)
            assert embedding is not None  # Should get an embedding from default embedder

    def test_store_and_retrieve(self, memory_store, mock_chromadb_client):
        """Test storing and retrieving items."""
        _, mock_collection = mock_chromadb_client

        # Create a test item
        item = MemoryItem(
            id="test-item-1",
            content="This is a test item",
            memory_type=MemoryType.WORKING,
            metadata={"test": "value"}
        )

        # Configure the mock collection to return the expected results
        mock_collection.get.return_value = {
            "ids": ["test-item-1"],
            "documents": ["This is a test item"],
            "metadatas": [{"test": "value", "memory_type": "working", "created_at": datetime.now().isoformat()}]
        }

        # Store the item
        item_id = memory_store.store(item)
        assert item_id == "test-item-1"

        # Verify the add method was called with the correct arguments
        mock_collection.add.assert_called_once()

        # Retrieve the item
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None
        assert retrieved_item.id == item_id
        assert retrieved_item.content == "This is a test item"
        assert retrieved_item.memory_type == MemoryType.WORKING
        assert retrieved_item.metadata.get("test") == "value"

    def test_search(self, memory_store, mock_chromadb_client):
        """Test searching for items."""
        _, mock_collection = mock_chromadb_client

        # Configure the mock collection to return the expected search results
        mock_collection.query.return_value = {
            "ids": [["item-1", "item-2"]],
            "documents": [["This is the first test item", "This is the second test item"]],
            "metadatas": [[
                {"index": 1, "memory_type": "working", "created_at": datetime.now().isoformat()},
                {"index": 2, "memory_type": "working", "created_at": datetime.now().isoformat()}
            ]],
            "distances": [[0.1, 0.2]]
        }

        # Create test items (we don't need to actually store them since we're mocking the collection)
        items = [
            MemoryItem(
                id="item-1",
                content="This is the first test item",
                memory_type=MemoryType.WORKING,
                metadata={"index": 1}
            ),
            MemoryItem(
                id="item-2",
                content="This is the second test item",
                memory_type=MemoryType.WORKING,
                metadata={"index": 2}
            )
        ]

        # Search for items
        results = memory_store.search({"query": "test item", "top_k": 2})

        # Verify the query method was called with the correct arguments
        mock_collection.query.assert_called_once()

        assert len(results) == 2

        # Verify that the results contain the expected items
        result_ids = [item.id for item in results]
        assert "item-1" in result_ids
        assert "item-2" in result_ids

    def test_delete(self, memory_store, mock_chromadb_client):
        """Test deleting items."""
        _, mock_collection = mock_chromadb_client

        # Configure the mock collection for the initial get
        mock_collection.get.return_value = {
            "ids": ["delete-test-item"],
            "documents": ["This is an item to delete"],
            "metadatas": [{"test": "delete", "memory_type": "working", "created_at": datetime.now().isoformat()}]
        }

        # Create and store a test item
        item = MemoryItem(
            id="delete-test-item",
            content="This is an item to delete",
            memory_type=MemoryType.WORKING,
            metadata={"test": "delete"}
        )

        item_id = memory_store.store(item)

        # Verify the item exists
        retrieved_item = memory_store.retrieve(item_id)
        assert retrieved_item is not None

        # Delete the item
        result = memory_store.delete(item_id)

        # Verify the delete method was called with the correct arguments
        mock_collection.delete.assert_called_once_with(ids=["delete-test-item"])

        assert result is True

        # Configure the mock collection to raise KeyError on the second get
        def get_side_effect(ids):
            if ids == ["delete-test-item"]:
                # Return empty results to trigger the KeyError in retrieve method
                return {
                    "ids": [],
                    "documents": [],
                    "metadatas": []
                }
            else:
                # For any other ID, return the original mock behavior
                return {
                    "ids": ["delete-test-item"],
                    "documents": ["This is an item to delete"],
                    "metadatas": [{"test": "delete", "memory_type": "working", "created_at": datetime.now().isoformat()}]
                }

        mock_collection.get.side_effect = get_side_effect

        # Verify the item no longer exists
        # The retrieve method will retry and eventually raise a RuntimeError with the KeyError as the cause
        with pytest.raises(RuntimeError) as excinfo:
            memory_store.retrieve(item_id)
        # Verify that the RuntimeError was caused by a KeyError
        assert "Item delete-test-item not found" in str(excinfo.value)
