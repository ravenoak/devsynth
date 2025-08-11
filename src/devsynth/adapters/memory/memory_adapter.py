"""Adapter that coordinates memory-related components."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Create a logger for this module early so optional imports can log failures
from devsynth.logging_setup import DevSynthLogger

from ...application.memory.context_manager import InMemoryStore, SimpleContextManager
from ...application.memory.duckdb_store import DuckDBStore
from ...application.memory.json_file_store import JSONFileStore
from ...application.memory.lmdb_store import LMDBStore
from ...application.memory.tinydb_store import TinyDBStore
from ...domain.interfaces.memory import ContextManager, MemoryStore, VectorStore

logger = DevSynthLogger(__name__)

try:  # pragma: no cover - optional dependency
    from ...application.memory.faiss_store import FAISSStore
except Exception as exc:  # pragma: no cover - graceful fallback
    logger.debug("FAISSStore unavailable: %s", exc)
    FAISSStore = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from ...application.memory.rdflib_store import RDFLibStore
except Exception as exc:  # pragma: no cover - graceful fallback
    logger.debug("RDFLibStore unavailable: %s", exc)
    RDFLibStore = None  # type: ignore[assignment]

from devsynth.exceptions import DevSynthError, MemoryStoreError

from ...adapters.kuzu_memory_store import KuzuMemoryStore
from ...adapters.memory.kuzu_adapter import KuzuAdapter
from ...application.memory.persistent_context_manager import PersistentContextManager
from ...config.settings import ensure_path_exists, get_settings


class MemorySystemAdapter:
    """Adapter coordinating memory stores and context managers.

    The adapter was historically a plain object with a dynamic ``__dict__``.
    Defining ``__slots__`` reduces its per-instance memory footprint and
    avoids the overhead of dynamically allocating attributes for the many
    memory-system configurations exercised in integration tests.
    """

    __slots__ = (
        "config",
        "storage_type",
        "memory_path",
        "max_context_size",
        "context_expiration_days",
        "vector_store_enabled",
        "provider_type",
        "chromadb_collection_name",
        "chromadb_host",
        "chromadb_port",
        "enable_chromadb",
        "encryption_at_rest",
        "encryption_key",
        "memory_store",
        "context_manager",
        "vector_store",
    )

    def __init__(
        self,
        config: Dict[str, Any] = None,
        memory_store: Optional[MemoryStore] = None,
        context_manager: Optional[ContextManager] = None,
        vector_store: Optional[VectorStore] = None,
        create_paths: bool = True,
    ):
        """
        Initialize the memory system adapter.

        Args:
            config: Optional configuration dictionary that overrides environment variables
            memory_store: Optional pre-configured memory store (for dependency injection)
            context_manager: Optional pre-configured context manager (for dependency injection)
            vector_store: Optional pre-configured vector store (for dependency injection)
            create_paths: Whether to create storage paths on initialization (default: True)
        """
        self.config = config or {}
        settings = get_settings()

        # Determine storage type from config or settings
        self.storage_type = self.config.get(
            "memory_store_type", settings.memory_store_type
        )
        self.memory_path = self.config.get(
            "memory_file_path", settings.memory_file_path
        )
        self.max_context_size = self.config.get(
            "max_context_size", settings.max_context_size
        )
        self.context_expiration_days = self.config.get(
            "context_expiration_days", settings.context_expiration_days
        )
        self.vector_store_enabled = self.config.get(
            "vector_store_enabled", settings.vector_store_enabled
        )
        self.provider_type = self.config.get(
            "provider_type", getattr(settings, "provider_type", None)
        )
        self.chromadb_collection_name = self.config.get(
            "chromadb_collection_name", settings.chromadb_collection_name
        )
        self.chromadb_host = self.config.get(
            "chromadb_host", getattr(settings, "chromadb_host", None)
        )
        self.chromadb_port = self.config.get(
            "chromadb_port", getattr(settings, "chromadb_port", 8000)
        )
        self.enable_chromadb = self.config.get(
            "enable_chromadb", getattr(settings, "enable_chromadb", False)
        )
        self.encryption_at_rest = self.config.get(
            "encryption_at_rest", getattr(settings, "encryption_at_rest", False)
        )
        self.encryption_key = self.config.get(
            "encryption_key", getattr(settings, "encryption_key", None)
        )

        # Support for direct dependency injection
        self.memory_store = memory_store
        self.context_manager = context_manager
        self.vector_store = vector_store

        # Initialize components only if they weren't injected
        if all(
            component is None
            for component in [memory_store, context_manager, vector_store]
        ):
            self._initialize_memory_system(create_paths=create_paths)
        else:
            # Log what components were injected
            injected = []
            if memory_store is not None:
                injected.append("memory_store")
            if context_manager is not None:
                injected.append("context_manager")
            if vector_store is not None:
                injected.append("vector_store")

            logger.info(
                f"Memory system initialized with injected components: {', '.join(injected)}"
            )

    def _initialize_memory_system(self, create_paths: bool = True):
        """
        Initialize the memory system with the current configuration.

        Args:
            create_paths: If True, ensure the memory directory exists
        """
        # Ensure the memory directory exists if needed and requested
        if create_paths and self.storage_type in ["file", "chromadb", "kuzu"]:
            self.memory_path = ensure_path_exists(self.memory_path, create=create_paths)

        # Initialize the appropriate store and context manager
        if self.storage_type == "file":
            self.memory_store = JSONFileStore(
                self.memory_path,
                encryption_enabled=self.encryption_at_rest,
                encryption_key=self.encryption_key,
            )
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # No vector store for file-based storage by default
            self.vector_store = None
        elif self.storage_type == "chromadb":
            if not self.enable_chromadb:
                logger.warning(
                    "ChromaDB support disabled via ENABLE_CHROMADB; falling back to in-memory store"
                )
                self.memory_store = InMemoryStore()
                self.context_manager = SimpleContextManager()
                self.vector_store = None
            else:
                try:
                    from ...adapters.memory.chroma_db_adapter import ChromaDBAdapter
                    from ...application.memory.chromadb_store import ChromaDBStore
                except Exception as e:  # pragma: no cover - optional dependency
                    logger.warning(
                        "ChromaDB dependencies not available: %s; using in-memory store",
                        e,
                    )
                    self.memory_store = InMemoryStore()
                    self.context_manager = SimpleContextManager()
                    self.vector_store = None
                else:
                    self.memory_store = ChromaDBStore(
                        self.memory_path,
                        host=self.chromadb_host,
                        port=self.chromadb_port,
                        collection_name=self.chromadb_collection_name,
                    )
                    self.context_manager = PersistentContextManager(
                        self.memory_path,
                        max_context_size=self.max_context_size,
                        expiration_days=self.context_expiration_days,
                    )
                    if self.vector_store_enabled:
                        self.vector_store = ChromaDBAdapter(
                            persist_directory=self.memory_path,
                            collection_name=self.chromadb_collection_name,
                            host=self.chromadb_host,
                            port=self.chromadb_port,
                        )
                    else:
                        self.vector_store = None
        elif self.storage_type == "kuzu":
            self.memory_store = KuzuMemoryStore(
                self.memory_path,
                provider_type=self.provider_type,
            )
            if (
                getattr(self.memory_store._store, "_use_fallback", False)
                and self.enable_chromadb
            ):
                logger.info("Kuzu unavailable; falling back to ChromaDB")
                try:
                    from ...adapters.memory.chroma_db_adapter import ChromaDBAdapter
                    from ...application.memory.chromadb_store import ChromaDBStore

                    self.memory_store = ChromaDBStore(
                        self.memory_path,
                        host=self.chromadb_host,
                        port=self.chromadb_port,
                        collection_name=self.chromadb_collection_name,
                    )
                    self.context_manager = PersistentContextManager(
                        self.memory_path,
                        max_context_size=self.max_context_size,
                        expiration_days=self.context_expiration_days,
                    )
                    if self.vector_store_enabled:
                        self.vector_store = ChromaDBAdapter(
                            persist_directory=self.memory_path,
                            collection_name=self.chromadb_collection_name,
                            host=self.chromadb_host,
                            port=self.chromadb_port,
                        )
                    else:
                        self.vector_store = None
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("ChromaDB fallback failed: %s", exc)
                    self.context_manager = PersistentContextManager(
                        self.memory_path,
                        max_context_size=self.max_context_size,
                        expiration_days=self.context_expiration_days,
                    )
                    if self.vector_store_enabled:
                        self.vector_store = self.memory_store.vector
                    else:
                        self.vector_store = None
            else:
                self.context_manager = PersistentContextManager(
                    self.memory_path,
                    max_context_size=self.max_context_size,
                    expiration_days=self.context_expiration_days,
                )
                if self.vector_store_enabled:
                    self.vector_store = self.memory_store.vector
                else:
                    self.vector_store = None
        elif self.storage_type == "tinydb":
            self.memory_store = TinyDBStore(
                self.memory_path,
                encryption_enabled=self.encryption_at_rest,
                encryption_key=self.encryption_key,
            )
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # No vector store for TinyDB-based storage by default
            self.vector_store = None
        elif self.storage_type == "duckdb":
            self.memory_store = DuckDBStore(self.memory_path)
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # DuckDBStore implements both MemoryStore and VectorStore interfaces
            if self.vector_store_enabled:
                self.vector_store = self.memory_store
            else:
                self.vector_store = None
        elif self.storage_type == "lmdb":
            self.memory_store = LMDBStore(
                self.memory_path,
                encryption_enabled=self.encryption_at_rest,
                encryption_key=self.encryption_key,
            )
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # No vector store for LMDB-based storage by default
            self.vector_store = None
        elif self.storage_type == "faiss":
            # FAISS is primarily a vector store, so we'll use it for vector storage
            # and use a different store for general memory items
            self.memory_store = JSONFileStore(
                self.memory_path,
                encryption_enabled=self.encryption_at_rest,
                encryption_key=self.encryption_key,
            )
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # Initialize FAISS vector store if enabled
            if self.vector_store_enabled:
                self.vector_store = FAISSStore(self.memory_path)
            else:
                self.vector_store = None
        elif self.storage_type == "rdflib":
            # RDFLib can serve as both a memory store and a vector store
            self.memory_store = RDFLibStore(self.memory_path)
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # RDFLibStore implements both MemoryStore and VectorStore interfaces
            if self.vector_store_enabled:
                self.vector_store = self.memory_store
            else:
                self.vector_store = None
        else:
            # Default to in-memory storage
            self.memory_store = InMemoryStore()
            self.context_manager = SimpleContextManager()
            self.vector_store = None

        logger.info(f"Initialized memory system with storage type: {self.storage_type}")
        if self.vector_store:
            if self.storage_type == "chromadb":
                logger.info(
                    f"Vector store enabled with ChromaDB collection: {self.chromadb_collection_name}"
                )
            elif self.storage_type == "kuzu":
                logger.info("Vector store enabled with Kuzu adapter")
            else:
                logger.info("Vector store enabled")

    def get_memory_store(self) -> MemoryStore:
        """Get the memory store."""
        return self.memory_store

    def get_context_manager(self) -> ContextManager:
        """Get the context manager."""
        return self.context_manager

    def get_vector_store(self) -> Optional[VectorStore]:
        """Get the vector store if available."""
        return self.vector_store

    def has_vector_store(self) -> bool:
        """Check if a vector store is available."""
        return self.vector_store is not None

    def get_token_usage(self) -> Dict[str, int]:
        """Get token usage statistics."""
        # Get token usage from store and context manager if they support it
        store_tokens = getattr(self.memory_store, "get_token_usage", lambda: 0)()
        context_tokens = getattr(self.context_manager, "get_token_usage", lambda: 0)()

        return {
            "memory_tokens": store_tokens,
            "context_tokens": context_tokens,
            "total_tokens": store_tokens + context_tokens,
        }

    def flush(self) -> None:
        """Flush underlying memory components to ensure persistence."""

        for component in (self.memory_store, self.context_manager, self.vector_store):
            if component is None:
                continue
            if hasattr(component, "flush"):
                try:
                    component.flush()
                except Exception:
                    logger.debug(
                        "Component %s flush failed",
                        type(component).__name__,
                        exc_info=True,
                    )

    def store(self, memory_item: Any) -> str:
        """
        Store a memory item in the memory store.

        This method delegates to the underlying memory store.

        Args:
            memory_item: The memory item to store

        Returns:
            The ID of the stored memory item
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")
        return self.memory_store.store(memory_item)

    def query_by_type(self, memory_type: Any) -> List[Any]:
        """
        Query memory items by type.

        This method delegates to the underlying memory store.
        If the memory store doesn't have a query_by_type method,
        it falls back to using the search method.

        Args:
            memory_type: The memory type to query for

        Returns:
            A list of memory items with the specified type
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        # Check if the memory store has a query_by_type method
        if hasattr(self.memory_store, "query_by_type"):
            return self.memory_store.query_by_type(memory_type)

        # Fall back to using the search method
        if hasattr(self.memory_store, "search"):
            # Convert MemoryType enum to string if needed
            if hasattr(memory_type, "value"):
                memory_type_value = memory_type.value
            else:
                memory_type_value = memory_type

            return self.memory_store.search({"memory_type": memory_type_value})

        # If neither method is available, return an empty list
        logger.warning(f"Memory store does not support query_by_type or search")
        return []

    def query_by_metadata(self, metadata: Dict[str, Any]) -> List[Any]:
        """
        Query memory items by metadata.

        This method delegates to the underlying memory store.
        If the memory store doesn't have a query_by_metadata method,
        it falls back to using the search method.

        Args:
            metadata: The metadata to query for

        Returns:
            A list of memory items with the specified metadata
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        # Check if the memory store has a query_by_metadata method
        if hasattr(self.memory_store, "query_by_metadata"):
            return self.memory_store.query_by_metadata(metadata)

        # Fall back to using the search method
        if hasattr(self.memory_store, "search"):
            return self.memory_store.search(metadata)

        # If neither method is available, return an empty list
        logger.warning(f"Memory store does not support query_by_metadata or search")
        return []

    def search(self, query: Dict[str, Any]) -> List[Any]:
        """
        Search for memory items matching the query.

        This method delegates to the underlying memory store.

        Args:
            query: The query to search for

        Returns:
            A list of memory items matching the query
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")
        return self.memory_store.search(query)

    def retrieve(self, item_id: str) -> Any:
        """
        Retrieve a memory item by ID.

        This method delegates to the underlying memory store.

        Args:
            item_id: The ID of the memory item to retrieve

        Returns:
            The retrieved memory item, or None if not found
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")
        return self.memory_store.retrieve(item_id)

    def get_all(self) -> List[Any]:
        """
        Get all memory items.

        This method delegates to the underlying memory store.

        Returns:
            A list of all memory items
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")
        return self.memory_store.get_all()

    def begin_transaction(self) -> str:
        """
        Begin a new transaction.

        This method delegates to the underlying memory store.
        If the memory store doesn't support transactions, a MemoryStoreError is raised.

        Returns:
            The ID of the new transaction

        Raises:
            MemoryStoreError: If the memory store doesn't support transactions or an error occurs
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        try:
            # Check if the memory store supports transactions
            if hasattr(self.memory_store, "begin_transaction"):
                return self.memory_store.begin_transaction()
            else:
                raise MemoryStoreError("Memory store does not support transactions")
        except Exception as e:
            logger.error(f"Error beginning transaction: {e}")
            raise MemoryStoreError(f"Error beginning transaction: {e}")

    def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction.

        This method delegates to the underlying memory store.
        If the memory store doesn't support transactions, a MemoryStoreError is raised.

        Args:
            transaction_id: The ID of the transaction to commit

        Returns:
            True if the transaction was committed successfully, False otherwise

        Raises:
            MemoryStoreError: If the memory store doesn't support transactions or an error occurs
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        try:
            # Check if the memory store supports transactions
            if hasattr(self.memory_store, "commit_transaction"):
                return self.memory_store.commit_transaction(transaction_id)
            else:
                raise MemoryStoreError("Memory store does not support transactions")
        except Exception as e:
            logger.error(f"Error committing transaction {transaction_id}: {e}")
            raise MemoryStoreError(
                f"Error committing transaction {transaction_id}: {e}"
            )

    def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction.

        This method delegates to the underlying memory store.
        If the memory store doesn't support transactions, a MemoryStoreError is raised.

        Args:
            transaction_id: The ID of the transaction to rollback

        Returns:
            True if the transaction was rolled back successfully, False otherwise

        Raises:
            MemoryStoreError: If the memory store doesn't support transactions or an error occurs
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        try:
            # Check if the memory store supports transactions
            if hasattr(self.memory_store, "rollback_transaction"):
                return self.memory_store.rollback_transaction(transaction_id)
            else:
                raise MemoryStoreError("Memory store does not support transactions")
        except Exception as e:
            logger.error(f"Error rolling back transaction {transaction_id}: {e}")
            raise MemoryStoreError(
                f"Error rolling back transaction {transaction_id}: {e}"
            )

    def is_transaction_active(self, transaction_id: str) -> bool:
        """
        Check if a transaction is active.

        This method delegates to the underlying memory store.
        If the memory store doesn't support transactions, a MemoryStoreError is raised.

        Args:
            transaction_id: The ID of the transaction to check

        Returns:
            True if the transaction is active, False otherwise

        Raises:
            MemoryStoreError: If the memory store doesn't support transactions or an error occurs
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        try:
            # Check if the memory store supports transactions
            if hasattr(self.memory_store, "is_transaction_active"):
                return self.memory_store.is_transaction_active(transaction_id)
            else:
                raise MemoryStoreError("Memory store does not support transactions")
        except Exception as e:
            logger.error(f"Error checking transaction {transaction_id} status: {e}")
            raise MemoryStoreError(
                f"Error checking transaction {transaction_id} status: {e}"
            )

    def execute_in_transaction(
        self, operations: List[callable], fallback_operations: List[callable] = None
    ) -> Any:
        """
        Execute a series of operations within a transaction.

        This method provides a high-level interface for executing operations within a transaction.
        If any operation fails, the transaction is rolled back and the fallback operations are executed.

        Args:
            operations: A list of callables to execute within the transaction
            fallback_operations: A list of callables to execute if the transaction fails

        Returns:
            The result of the last operation

        Raises:
            MemoryStoreError: If the memory store doesn't support transactions or an error occurs
        """
        if self.memory_store is None:
            raise ValueError("Memory store is not initialized")

        # Begin a transaction
        transaction_id = self.begin_transaction()

        try:
            # Execute the operations
            result = None
            for operation in operations:
                result = operation()

            # Commit the transaction
            self.commit_transaction(transaction_id)

            return result
        except Exception as e:
            # Rollback the transaction
            logger.error(
                f"Error executing operations in transaction {transaction_id}: {e}"
            )
            self.rollback_transaction(transaction_id)

            # Execute fallback operations if provided
            if fallback_operations:
                try:
                    for operation in fallback_operations:
                        operation()
                except Exception as fallback_error:
                    logger.error(
                        f"Error executing fallback operations: {fallback_error}"
                    )

            # Re-raise the original error
            raise MemoryStoreError(f"Error executing operations in transaction: {e}")

    @classmethod
    def create_for_testing(
        cls,
        storage_type: str = "memory",
        memory_path: Optional[Union[str, Path]] = None,
    ) -> "MemorySystemAdapter":
        """
        Create a memory system adapter configured specifically for testing.

        This factory method creates an adapter with a given storage type and path,
        using in-memory stores by default for isolation. This makes tests hermetic
        by avoiding file system side effects.

        Args:
            storage_type: Type of storage to use ("memory", "file", or "chromadb")
            memory_path: Optional path for file-based storage

        Returns:
            An initialized MemorySystemAdapter suitable for testing
        """
        config = {
            "memory_store_type": storage_type,
            "max_context_size": 1000,  # Small context size for tests
            "context_expiration_days": 1,  # Short expiration for tests
            "vector_store_enabled": storage_type in ["chromadb", "kuzu"],
        }

        if memory_path:
            config["memory_file_path"] = str(memory_path)

        # Create with create_paths=False by default for tests
        # Tests should explicitly create paths if needed
        return cls(config=config, create_paths=False)
