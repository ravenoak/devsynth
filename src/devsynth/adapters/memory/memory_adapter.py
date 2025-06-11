"""Adapter that coordinates memory-related components."""

import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from ...domain.interfaces.memory import MemoryStore, ContextManager, VectorStore
from ...application.memory.context_manager import InMemoryStore, SimpleContextManager
from ...application.memory.json_file_store import JSONFileStore
from ...application.memory.chromadb_store import ChromaDBStore
from ...application.memory.tinydb_store import TinyDBStore
from ...application.memory.duckdb_store import DuckDBStore
from ...application.memory.lmdb_store import LMDBStore
from ...application.memory.faiss_store import FAISSStore
from ...application.memory.rdflib_store import RDFLibStore
from ...application.memory.persistent_context_manager import PersistentContextManager
from ...adapters.memory.chroma_db_adapter import ChromaDBAdapter
from ...config.settings import get_settings, ensure_path_exists

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError


class MemorySystemAdapter:
    """
    Adapter for the memory system.

    This class provides a unified interface to the memory components (store, context manager,
    and vector store). It supports dependency injection for improved testability and
    deferred path creation for better test isolation.
    """

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
        self.chromadb_collection_name = self.config.get(
            "chromadb_collection_name", settings.chromadb_collection_name
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
        if create_paths and self.storage_type in ["file", "chromadb"]:
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
            self.memory_store = ChromaDBStore(self.memory_path)
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days,
            )
            # Initialize vector store if enabled
            if self.vector_store_enabled:
                self.vector_store = ChromaDBAdapter(
                    persist_directory=self.memory_path,
                    collection_name=self.chromadb_collection_name,
                )
            else:
                self.vector_store = None
        elif self.storage_type == "tinydb":
            self.memory_store = TinyDBStore(self.memory_path)
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
            self.memory_store = LMDBStore(self.memory_path)
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
            logger.info(
                f"Vector store enabled with ChromaDB collection: {self.chromadb_collection_name}"
            )

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
            "vector_store_enabled": storage_type == "chromadb",
        }

        if memory_path:
            config["memory_file_path"] = str(memory_path)

        # Create with create_paths=False by default for tests
        # Tests should explicitly create paths if needed
        return cls(config=config, create_paths=False)
