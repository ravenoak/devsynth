import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import Any, Dict, List, Optional, Union, ContextManager
import os
import logging
import time
import atexit
import sys
from contextlib import contextmanager
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from datetime import datetime
from devsynth.adapters.provider_system import get_provider, embed, ProviderError
from devsynth.logging_setup import DevSynthLogger

# Global registry to track ChromaDB clients and ensure proper cleanup
_chromadb_clients = {}

@atexit.register
def _cleanup_chromadb_clients():
    """Clean up all ChromaDB clients at program exit."""
    global _chromadb_clients
    for client_id, client in list(_chromadb_clients.items()):
        try:
            if hasattr(client, 'close'):
                client.close()
            _chromadb_clients.pop(client_id, None)
        except Exception as e:
            # Just log errors during cleanup, don't raise
            logging.error(f"Error cleaning up ChromaDB client {client_id}: {e}")

@contextmanager
def chromadb_client_context(persist_directory: str, instance_id: str = None) -> ContextManager[chromadb.Client]:
    """
    Context manager for ChromaDB clients to ensure proper resource management.

    Args:
        persist_directory: Directory to persist ChromaDB data
        instance_id: Optional unique identifier for this instance, used to ensure isolation in tests

    Yields:
        ChromaDB client instance
    """
    # Create a unique client ID
    unique_id = f"{instance_id}_{time.time()}" if instance_id else f"client_{time.time()}"
    client_id = f"client_{unique_id}"

    # Ensure we're using a unique directory for each test
    actual_persist_dir = persist_directory
    if 'pytest' in sys.modules:
        # In test environments, create a unique subdirectory
        actual_persist_dir = os.path.join(persist_directory, unique_id)
        os.makedirs(actual_persist_dir, exist_ok=True)

    client = None

    try:
        # Create a new client with the unique persist directory
        settings = Settings(
            persist_directory=actual_persist_dir,
            anonymized_telemetry=False  # Disable telemetry
        )

        client = chromadb.Client(settings)
        _chromadb_clients[client_id] = client
        logging.debug(f"Created new ChromaDB client with ID {client_id} in directory {actual_persist_dir}")

        yield client
    finally:
        # Always close the client when done
        try:
            if client and hasattr(client, 'close'):
                client.close()
            _chromadb_clients.pop(client_id, None)
            logging.debug(f"Closed ChromaDB client {client_id}")
        except Exception as e:
            logging.warning(f"Error closing ChromaDB client {client_id}: {e}")

class ChromaDBMemoryStore(MemoryStore):
    """
    ChromaDB-backed implementation of the MemoryStore interface.
    Stores and retrieves artifacts with semantic search using embeddings.

    Integrates with the provider system to leverage either OpenAI or LM Studio
    for embeddings, with automatic fallback if a provider fails.
    """
    def __init__(self,
                persist_directory: str = ".devsynth/chromadb_store",
                use_provider_system: bool = True,
                provider_type: Optional[str] = None,
                collection_name: str = "devsynth_artifacts",
                max_retries: int = 3,
                retry_delay: float = 0.5,
                instance_id: str = None):
        """
        Initialize the ChromaDB memory store.

        Args:
            persist_directory: Directory to persist ChromaDB data
            use_provider_system: Whether to use the provider system for embeddings
            provider_type: Optional specific provider to use (if use_provider_system is True)
            collection_name: Name of the ChromaDB collection to use
            max_retries: Maximum number of retries for ChromaDB operations
            retry_delay: Delay between retries in seconds
            instance_id: Optional unique identifier for this instance, used to ensure isolation in tests
        """
        # Setup logging
        self.logger = DevSynthLogger(__name__)

        # Store configuration
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.instance_id = instance_id or f"instance_{time.time()}"  # Generate a unique ID if none provided

        # Ensure the persist directory exists
        try:
            os.makedirs(persist_directory, exist_ok=True)
            self.logger.info(f"ChromaDB persist directory ensured: {persist_directory}")
        except Exception as e:
            self.logger.error(f"Failed to create ChromaDB persist directory: {e}")
            raise RuntimeError(f"Failed to create ChromaDB persist directory: {e}")

        # Initialize ChromaDB client with error handling and retries
        retry_count = 0
        last_exception = None

        while retry_count < max_retries:
            try:
                with chromadb_client_context(persist_directory, instance_id=self.instance_id) as client:
                    self.client = client
                    self.logger.info(f"ChromaDB client initialized with persist directory: {persist_directory}, instance_id: {self.instance_id}")

                    # Create or get collection with error handling
                    self.collection = client.get_or_create_collection(collection_name)
                    self.logger.info(f"ChromaDB collection initialized: {collection_name}")

                    # If we get here, initialization was successful
                    break
            except Exception as e:
                last_exception = e
                retry_count += 1
                self.logger.warning(f"ChromaDB initialization attempt {retry_count} failed: {e}")

                if retry_count < max_retries:
                    # Wait before retrying
                    time.sleep(retry_delay)
                else:
                    self.logger.error(f"Failed to initialize ChromaDB after {max_retries} attempts: {e}")
                    raise RuntimeError(f"Failed to initialize ChromaDB after {max_retries} attempts: {e}") from last_exception

        # Use provider system for embeddings if specified, otherwise fallback to default
        self.use_provider_system = use_provider_system
        self.provider_type = provider_type
        self.logger.info(f"Provider system usage: {use_provider_system}, Provider type: {provider_type}")

        # Initialize default embedder - will be used if provider system is disabled or fails
        try:
            self.embedder = embedding_functions.DefaultEmbeddingFunction()
            self.logger.info("Default embedding function initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize default embedding function: {e}")
            raise RuntimeError(f"Failed to initialize default embedding function: {e}")

        # Register cleanup method
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Clean up resources when the instance is destroyed."""
        self.logger.debug(f"Cleaning up ChromaDBMemoryStore resources for {self.collection_name}")

        # Explicitly close the client and remove it from the global registry
        client_id = f"client_{self.persist_directory}"
        if client_id in _chromadb_clients:
            try:
                client = _chromadb_clients[client_id]
                if hasattr(client, 'close'):
                    client.close()
                _chromadb_clients.pop(client_id, None)
                self.logger.debug(f"Closed ChromaDB client for {self.persist_directory}")
            except Exception as e:
                self.logger.warning(f"Error closing ChromaDB client for {self.persist_directory}: {e}")

    def _with_retries(self, operation_name, operation_func, *args, **kwargs):
        """
        Execute an operation with retries.

        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the operation

        Raises:
            RuntimeError: If the operation fails after all retries
        """
        retry_count = 0
        last_exception = None

        while retry_count < self.max_retries:
            try:
                result = operation_func(*args, **kwargs)
                if retry_count > 0:
                    self.logger.info(f"{operation_name} succeeded after {retry_count + 1} attempts")
                return result
            except Exception as e:
                last_exception = e
                retry_count += 1
                self.logger.warning(f"{operation_name} attempt {retry_count} failed: {e}")

                if retry_count < self.max_retries:
                    # Wait before retrying
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"{operation_name} failed after {self.max_retries} attempts: {e}")
                    raise RuntimeError(f"{operation_name} failed after {self.max_retries} attempts: {e}") from last_exception

    def _get_embedding(self, text: Union[str, List[str]]) -> List[float]:
        """
        Get embedding for text using the provider system or default embedder.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.use_provider_system:
            try:
                self.logger.debug(f"Attempting to get embedding using provider system with type: {self.provider_type}")
                # Use provider system with fallback
                embedding_results = embed(text, provider_type=self.provider_type, fallback=True)

                # Validate embedding results
                if not embedding_results or (isinstance(embedding_results, list) and len(embedding_results) == 0):
                    raise ValueError("Provider system returned empty embedding results")

                # Provider system returns list of embeddings, take first one for single text
                if isinstance(text, str):
                    self.logger.debug("Successfully obtained embedding for single text from provider system")
                    return embedding_results[0]

                self.logger.debug(f"Successfully obtained embeddings for {len(embedding_results)} texts from provider system")
                return embedding_results

            except (ProviderError, ValueError, IndexError, TypeError) as e:
                # Log specific error and fall back to default embedder
                self.logger.warning(f"Provider system embedding failed with {type(e).__name__}: {e}. Falling back to default embedder.")

            except Exception as e:
                # Log unexpected errors
                self.logger.error(f"Unexpected error during provider embedding: {type(e).__name__}: {e}. Falling back to default embedder.")

            # If we reach here, provider system failed, use default embedder
            try:
                # Ensure default embedder is initialized
                if not hasattr(self, 'embedder') or self.embedder is None:
                    self.logger.info("Initializing default embedding function for fallback")
                    self.embedder = embedding_functions.DefaultEmbeddingFunction()

                self.logger.debug("Using default embedder as fallback")
                return self.embedder(text)
            except Exception as e:
                self.logger.error(f"Default embedder also failed: {e}")
                raise RuntimeError(f"Both provider system and default embedder failed: {e}")
        else:
            # Use default embedder
            try:
                # Ensure embedder is initialized
                if not hasattr(self, 'embedder') or self.embedder is None:
                    self.logger.info("Initializing default embedding function")
                    self.embedder = embedding_functions.DefaultEmbeddingFunction()

                self.logger.debug("Using default embedder (provider system disabled)")
                return self.embedder(text)
            except Exception as e:
                self.logger.error(f"Default embedder failed: {e}")
                raise RuntimeError(f"Default embedder failed: {e}")

    def store(self, item: MemoryItem) -> str:
        """
        Store a memory item.

        Args:
            item: The memory item to store

        Returns:
            The ID of the stored item
        """
        content = item.content
        metadata = dict(item.metadata or {})
        metadata["memory_type"] = item.memory_type.value if hasattr(item.memory_type, 'value') else str(item.memory_type)
        metadata["created_at"] = item.created_at.isoformat() if item.created_at else datetime.now().isoformat()

        # Use provider system for embeddings
        embedding = self._get_embedding(content)

        item_id = item.id or str(hash(content))

        def _store_operation():
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[item_id],
                embeddings=[embedding],
            )
            return item_id

        return self._with_retries("Store operation", _store_operation)

    def retrieve(self, item_id: str) -> MemoryItem:
        """
        Retrieve a memory item by ID.

        Args:
            item_id: The ID of the item to retrieve

        Returns:
            The retrieved memory item

        Raises:
            KeyError: If the item is not found
        """
        def _retrieve_operation():
            results = self.collection.get(ids=[item_id])
            if not results["documents"]:
                raise KeyError(f"Item {item_id} not found.")
            doc = results["documents"][0]
            meta = results["metadatas"][0]
            return MemoryItem(
                id=item_id,
                content=doc,
                memory_type=MemoryType(meta.get("memory_type", "WORKING")),
                metadata=meta,
                created_at=datetime.fromisoformat(meta["created_at"]) if "created_at" in meta else datetime.now(),
            )

        return self._with_retries("Retrieve operation", _retrieve_operation)

    def search(self, query: dict) -> list:
        """
        Search for memory items.

        Args:
            query: A dictionary with 'query' and optional 'top_k' keys

        Returns:
            A list of memory items matching the query
        """
        # Accepts a dict with 'query' and optional 'top_k'
        query_text = query.get("query")
        top_k = query.get("top_k", 5)

        # Use provider system for embeddings
        embedding = self._get_embedding(query_text)

        def _search_operation():
            results = self.collection.query(query_embeddings=[embedding], n_results=top_k)

            # Handle empty results
            if not results["documents"] or len(results["documents"][0]) == 0:
                self.logger.warning(f"No results found for query: {query_text}")
                return []

            items = []
            for doc, meta, id_ in zip(results["documents"][0], results["metadatas"][0], results["ids"][0]):
                items.append(MemoryItem(
                    id=id_,
                    content=doc,
                    memory_type=MemoryType(meta.get("memory_type", "WORKING")),
                    metadata=meta,
                    created_at=datetime.fromisoformat(meta["created_at"]) if "created_at" in meta else datetime.now(),
                ))
            return items

        return self._with_retries("Search operation", _search_operation)

    def delete(self, item_id: str) -> bool:
        """
        Delete a memory item by ID.

        Args:
            item_id: The ID of the item to delete

        Returns:
            True if the item was deleted, False otherwise
        """
        def _delete_operation():
            self.collection.delete(ids=[item_id])
            return True

        return self._with_retries("Delete operation", _delete_operation)
