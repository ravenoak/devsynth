# Feature: ChromaDB memory store
try:
    from chromadb.api import ClientAPI
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError as e:  # pragma: no cover - optional dependency
    raise ImportError(
        "ChromaDBMemoryStore requires the 'chromadb' package. Install it with 'pip install chromadb' or use the dev extras."
    ) from e
import atexit
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, ContextManager, Dict, List, Optional, Union

from devsynth.adapters.provider_system import ProviderError, embed
from devsynth.config.settings import ensure_path_exists
from devsynth.domain.interfaces.memory import MemoryStore
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger

# Global registry to track ChromaDB clients and ensure proper cleanup
_chromadb_clients = {}


@atexit.register
def _cleanup_chromadb_clients():
    """Clean up all ChromaDB clients at program exit."""
    for client_id, client in list(_chromadb_clients.items()):
        try:
            if hasattr(client, "close"):
                client.close()
            _chromadb_clients.pop(client_id, None)
        except Exception as e:
            # Just log errors during cleanup, don't raise
            logging.error(f"Error cleaning up ChromaDB client {client_id}: {e}")


@contextmanager
def chromadb_client_context(
    persist_directory: str, instance_id: str = None
) -> ContextManager[ClientAPI]:
    """
    Context manager for ChromaDB clients to ensure proper resource management.

    Args:
        persist_directory: Directory to persist ChromaDB data
        instance_id: Optional unique identifier for this instance, used to ensure isolation in tests

    Yields:
        ChromaDB client instance
    """
    # Create a unique client ID
    unique_id = (
        f"{instance_id}_{time.time()}" if instance_id else f"client_{time.time()}"
    )
    client_id = f"client_{unique_id}"

    # Ensure we're using a unique directory for each test
    actual_persist_dir = persist_directory
    if "pytest" in sys.modules:
        # In test environments, create a unique subdirectory
        actual_persist_dir = os.path.join(persist_directory, unique_id)
        # Use ensure_path_exists to respect test isolation
        ensure_path_exists(actual_persist_dir)

    client = None

    try:
        # Create a new client with the unique persist directory
        settings = Settings(
            persist_directory=actual_persist_dir,
            anonymized_telemetry=False,  # Disable telemetry
        )

        client = ClientAPI(settings)
        _chromadb_clients[client_id] = client
        logging.debug(
            f"Created new ChromaDB client with ID {client_id} in directory {actual_persist_dir}"
        )

        yield client
    finally:
        # Always close the client when done
        try:
            if client and hasattr(client, "close"):
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

    Supports transactions for atomic operations across multiple store/retrieve/delete
    operations, with commit and rollback capabilities.
    """

    def __init__(
        self,
        persist_directory: str = None,
        use_provider_system: bool = True,
        provider_type: str | None = None,
        collection_name: str = "devsynth_artifacts",
        max_retries: int = 3,
        retry_delay: float = 0.5,
        instance_id: str = None,
    ):
        """
        Initialize the ChromaDB memory store.

        Args:
            persist_directory: Directory to persist ChromaDB data. If None, uses DEVSYNTH_PROJECT_DIR or current directory.
            use_provider_system: Whether to use the provider system for embeddings
            provider_type: Optional specific provider to use (if use_provider_system is True)
            collection_name: Name of the ChromaDB collection to use
            max_retries: Maximum number of retries for ChromaDB operations
            retry_delay: Delay between retries in seconds
            instance_id: Optional unique identifier for this instance, used to ensure isolation in tests
        """
        # Setup logging
        self.logger = DevSynthLogger(__name__)

        # Transaction support
        self._active_transactions = {}  # Maps transaction_id to transaction data
        self._transaction_operations = {}  # Maps transaction_id to list of operations

        # Determine the persist directory based on environment variables
        if persist_directory is None:
            # Use DEVSYNTH_PROJECT_DIR if set (for test isolation)
            project_dir = os.environ.get("DEVSYNTH_PROJECT_DIR")
            if project_dir:
                persist_directory = os.path.join(
                    project_dir, ".devsynth", "chromadb_store"
                )
                self.logger.debug(
                    f"Using test environment for ChromaDB store: {persist_directory}"
                )
            else:
                # Default to current working directory
                persist_directory = os.path.join(
                    os.getcwd(), ".devsynth", "chromadb_store"
                )
                self.logger.debug(
                    f"Using current directory for ChromaDB store: {persist_directory}"
                )

        # Store configuration
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.instance_id = (
            instance_id or f"instance_{time.time()}"
        )  # Generate a unique ID if none provided

        # Ensure the persist directory exists using the settings utility function
        # This respects test isolation by checking DEVSYNTH_NO_FILE_LOGGING
        try:
            ensure_path_exists(persist_directory)
            self.logger.info(f"ChromaDB persist directory ensured: {persist_directory}")
        except Exception as e:
            self.logger.error(f"Failed to create ChromaDB persist directory: {e}")
            raise RuntimeError(f"Failed to create ChromaDB persist directory: {e}")

        # Initialize ChromaDB client with error handling and retries
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Use a context manager so the client is always cleaned up
                self._client_ctx = chromadb_client_context(
                    persist_directory, instance_id=self.instance_id
                )
                self.client = self._client_ctx.__enter__()

                self.logger.info(
                    "ChromaDB client initialized with persist directory: %s, instance_id: %s",
                    persist_directory,
                    self.instance_id,
                )

                # Create or get collection with error handling
                self.collection = self.client.get_or_create_collection(collection_name)
                self.logger.info(f"ChromaDB collection initialized: {collection_name}")

                # If we get here, initialization was successful
                break
            except Exception as e:
                last_exception = e
                retry_count += 1
                self.logger.warning(
                    f"ChromaDB initialization attempt {retry_count} failed: {e}"
                )

                if retry_count < max_retries:
                    # Wait before retrying
                    time.sleep(retry_delay)
                else:
                    self.logger.error(
                        f"Failed to initialize ChromaDB after {max_retries} attempts: {e}"
                    )
                    raise RuntimeError(
                        f"Failed to initialize ChromaDB after {max_retries} attempts: {e}"
                    )

        # Use provider system for embeddings if specified, otherwise fallback to default
        self.use_provider_system = use_provider_system
        self.provider_type = provider_type
        self.logger.info(
            f"Provider system usage: {use_provider_system}, Provider type: {provider_type}"
        )

        # Initialize default embedder - will be used if provider system is disabled or fails
        try:
            self.embedder = embedding_functions.DefaultEmbeddingFunction()
            self.logger.info("Default embedding function initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize default embedding function: {e}")
            raise RuntimeError(f"Failed to initialize default embedding function: {e}")

        # Register cleanup method
        atexit.register(self._cleanup)

    def close(self) -> None:
        """Close the ChromaDB client and release resources."""
        ctx = getattr(self, "_client_ctx", None)
        if ctx:
            try:
                ctx.__exit__(None, None, None)
            except Exception as e:  # pragma: no cover - best effort cleanup
                self.logger.warning(f"Error closing ChromaDB client: {e}")
            finally:
                self._client_ctx = None
                self.client = None

    def _cleanup(self) -> None:
        """Clean up resources when the instance is destroyed."""
        self.logger.debug(
            f"Cleaning up ChromaDBMemoryStore resources for {self.collection_name}"
        )
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:  # pragma: no cover - defensive
            pass

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
                    self.logger.info(
                        f"{operation_name} succeeded after {retry_count + 1} attempts"
                    )
                return result
            except Exception as e:
                last_exception = e
                retry_count += 1
                self.logger.warning(
                    f"{operation_name} attempt {retry_count} failed: {e}"
                )

                if retry_count < self.max_retries:
                    # Wait before retrying
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(
                        f"{operation_name} failed after {self.max_retries} attempts: {e}"
                    )
                    raise RuntimeError(
                        f"{operation_name} failed after {self.max_retries} attempts: {e}"
                    ) from last_exception

    def _get_embedding(self, text: str | list[str]) -> list[float]:
        """
        Get embedding for text using the provider system or default embedder.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.use_provider_system:
            try:
                self.logger.debug(
                    f"Attempting to get embedding using provider system with type: {self.provider_type}"
                )
                # Use provider system with fallback
                embedding_results = embed(
                    text, provider_type=self.provider_type, fallback=True
                )

                # Validate embedding results
                if not embedding_results or (
                    isinstance(embedding_results, list) and len(embedding_results) == 0
                ):
                    raise ValueError("Provider system returned empty embedding results")

                # Provider system returns list of embeddings, take first one for single text
                if isinstance(text, str):
                    self.logger.debug(
                        "Successfully obtained embedding for single text from provider system"
                    )
                    return embedding_results[0]

                self.logger.debug(
                    f"Successfully obtained embeddings for {len(embedding_results)} texts from provider system"
                )
                return embedding_results

            except (ProviderError, ValueError, IndexError, TypeError) as e:
                # Log specific error and fall back to default embedder
                self.logger.warning(
                    f"Provider system embedding failed with {type(e).__name__}: {e}. Falling back to default embedder."
                )

            except Exception as e:
                # Log unexpected errors
                self.logger.error(
                    f"Unexpected error during provider embedding: {type(e).__name__}: {e}. Falling back to default embedder."
                )

            # If we reach here, provider system failed, use default embedder
            try:
                # Ensure default embedder is initialized
                if not hasattr(self, "embedder") or self.embedder is None:
                    self.logger.info(
                        "Initializing default embedding function for fallback"
                    )
                    self.embedder = embedding_functions.DefaultEmbeddingFunction()

                self.logger.debug("Using default embedder as fallback")
                return self.embedder(text)
            except Exception as e:
                self.logger.error(f"Default embedder also failed: {e}")
                raise RuntimeError(
                    f"Both provider system and default embedder failed: {e}"
                )
        else:
            # Use default embedder
            try:
                # Ensure embedder is initialized
                if not hasattr(self, "embedder") or self.embedder is None:
                    self.logger.info("Initializing default embedding function")
                    self.embedder = embedding_functions.DefaultEmbeddingFunction()

                self.logger.debug("Using default embedder (provider system disabled)")
                return self.embedder(text)
            except Exception as e:
                self.logger.error(f"Default embedder failed: {e}")
                raise RuntimeError(f"Default embedder failed: {e}")

    def store(self, item: MemoryItem, transaction_id: str = None) -> str:
        """
        Store a memory item.

        Args:
            item: The memory item to store
            transaction_id: Optional transaction ID to add this operation to a transaction

        Returns:
            The ID of the stored item
        """
        content = item.content
        metadata = dict(item.metadata or {})
        metadata["memory_type"] = (
            item.memory_type.value
            if hasattr(item.memory_type, "value")
            else str(item.memory_type)
        )
        metadata["created_at"] = (
            item.created_at.isoformat()
            if item.created_at
            else datetime.now().isoformat()
        )

        # Use provider system for embeddings
        embedding = self._get_embedding(content)

        item_id = item.id or str(hash(content))

        # If this is part of a transaction, add to transaction and return
        if transaction_id and self.is_transaction_active(transaction_id):
            operation_data = {"item": item, "embedding": embedding, "item_id": item_id}
            self.add_to_transaction(transaction_id, "store", operation_data)
            self.logger.debug(
                f"Added store operation for item {item_id} to transaction {transaction_id}"
            )
            return item_id

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
                created_at=(
                    datetime.fromisoformat(meta["created_at"])
                    if "created_at" in meta
                    else datetime.now()
                ),
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
            results = self.collection.query(
                query_embeddings=[embedding], n_results=top_k
            )

            # Handle empty results
            if not results["documents"] or len(results["documents"][0]) == 0:
                self.logger.warning(f"No results found for query: {query_text}")
                return []

            items = []
            for doc, meta, id_ in zip(
                results["documents"][0], results["metadatas"][0], results["ids"][0]
            ):
                items.append(
                    MemoryItem(
                        id=id_,
                        content=doc,
                        memory_type=MemoryType(meta.get("memory_type", "WORKING")),
                        metadata=meta,
                        created_at=(
                            datetime.fromisoformat(meta["created_at"])
                            if "created_at" in meta
                            else datetime.now()
                        ),
                    )
                )
            return items

        return self._with_retries("Search operation", _search_operation)

    def delete(self, item_id: str, transaction_id: str = None) -> bool:
        """
        Delete a memory item by ID.

        Args:
            item_id: The ID of the item to delete
            transaction_id: Optional transaction ID to add this operation to a transaction

        Returns:
            True if the item was deleted, False otherwise
        """
        # If this is part of a transaction, add to transaction and return
        if transaction_id and self.is_transaction_active(transaction_id):
            operation_data = {"item_id": item_id}
            self.add_to_transaction(transaction_id, "delete", operation_data)
            self.logger.debug(
                f"Added delete operation for item {item_id} to transaction {transaction_id}"
            )
            return True

        def _delete_operation():
            self.collection.delete(ids=[item_id])
            return True

        return self._with_retries("Delete operation", _delete_operation)

    def get_all_items(self) -> list[MemoryItem]:
        """Return all stored :class:`MemoryItem` objects."""

        def _get_operation():
            result = self.collection.get(include=["documents", "metadatas"])
            items: list[MemoryItem] = []
            docs = result.get("documents", [])
            metas = result.get("metadatas", [])
            ids = result.get("ids", [])

            # Handle both flat and nested array structures
            # ChromaDB can return either format depending on the context
            if docs and isinstance(docs[0], list):
                # Nested array format
                docs = docs[0] if docs else []
                metas = metas[0] if metas else []

            for idx, item_id in enumerate(ids):
                doc = docs[idx] if idx < len(docs) else None
                meta = metas[idx] if idx < len(metas) else {}
                items.append(
                    MemoryItem(
                        id=item_id,
                        content=doc,
                        memory_type=MemoryType(meta.get("memory_type", "WORKING")),
                        metadata=meta,
                        created_at=(
                            datetime.fromisoformat(meta["created_at"])
                            if "created_at" in meta
                            else datetime.now()
                        ),
                    )
                )
            return items

        return self._with_retries("Get all items", _get_operation)

    def begin_transaction(self) -> str:
        """Begin a new transaction and return a transaction ID.

        Transactions provide atomicity for a series of operations.
        All operations within a transaction either succeed or fail together.

        Returns:
            str: A unique transaction ID
        """
        # Generate a unique transaction ID
        transaction_id = f"tx_{time.time()}_{hash(str(time.time()))}"

        # Initialize transaction data
        self._active_transactions[transaction_id] = {
            "started_at": datetime.now(),
            "status": "active",
            "operations": [],
        }

        # Initialize operations list
        self._transaction_operations[transaction_id] = []

        self.logger.debug(f"Transaction {transaction_id} started")
        return transaction_id

    def commit_transaction(self, transaction_id: str) -> bool:
        """Commit a transaction, making all its operations permanent.

        Args:
            transaction_id: The ID of the transaction to commit

        Returns:
            bool: True if the transaction was committed successfully, False otherwise
        """
        # Check if transaction exists and is active
        if not self.is_transaction_active(transaction_id):
            self.logger.warning(
                f"Cannot commit transaction {transaction_id}: not active or doesn't exist"
            )
            return False

        try:
            # Execute all pending operations in the transaction
            operations = self._transaction_operations.get(transaction_id, [])

            for op in operations:
                op_type = op.get("type")
                op_data = op.get("data", {})

                if op_type == "store":
                    # Execute store operation
                    item = op_data.get("item")
                    if item:
                        self.store(item)
                elif op_type == "delete":
                    # Execute delete operation
                    item_id = op_data.get("item_id")
                    if item_id:
                        self.delete(item_id)
                # Add other operation types as needed

            # Mark transaction as committed
            self._active_transactions[transaction_id]["status"] = "committed"
            self.logger.debug(f"Transaction {transaction_id} committed successfully")

            # Clean up
            self._transaction_operations.pop(transaction_id, None)

            return True
        except Exception as e:
            # Log error and mark transaction as failed
            self.logger.error(f"Error committing transaction {transaction_id}: {e}")
            self._active_transactions[transaction_id]["status"] = "failed"
            self._active_transactions[transaction_id]["error"] = str(e)

            # Clean up
            self._transaction_operations.pop(transaction_id, None)

            return False

    def rollback_transaction(self, transaction_id: str) -> bool:
        """Rollback a transaction, undoing all its operations.

        Args:
            transaction_id: The ID of the transaction to rollback

        Returns:
            bool: True if the transaction was rolled back successfully, False otherwise
        """
        # Check if transaction exists
        if transaction_id not in self._active_transactions:
            self.logger.warning(
                f"Cannot rollback transaction {transaction_id}: doesn't exist"
            )
            return False

        # Mark transaction as rolled back
        self._active_transactions[transaction_id]["status"] = "rolled_back"
        self.logger.debug(f"Transaction {transaction_id} rolled back")

        # Clean up
        self._transaction_operations.pop(transaction_id, None)

        return True

    def is_transaction_active(self, transaction_id: str) -> bool:
        """Check if a transaction is active.

        Args:
            transaction_id: The ID of the transaction to check

        Returns:
            bool: True if the transaction is active, False otherwise
        """
        transaction = self._active_transactions.get(transaction_id)
        return transaction is not None and transaction.get("status") == "active"

    def add_to_transaction(
        self, transaction_id: str, operation_type: str, operation_data: dict[str, Any]
    ) -> bool:
        """Add an operation to a transaction.

        Args:
            transaction_id: The ID of the transaction
            operation_type: The type of operation (store, delete, etc.)
            operation_data: The data for the operation

        Returns:
            bool: True if the operation was added successfully, False otherwise
        """
        if not self.is_transaction_active(transaction_id):
            self.logger.warning(
                f"Cannot add operation to transaction {transaction_id}: not active or doesn't exist"
            )
            return False

        # Add operation to transaction
        operation = {
            "type": operation_type,
            "data": operation_data,
            "timestamp": datetime.now().isoformat(),
        }

        self._transaction_operations.setdefault(transaction_id, []).append(operation)
        self.logger.debug(
            f"Added {operation_type} operation to transaction {transaction_id}"
        )

        return True
