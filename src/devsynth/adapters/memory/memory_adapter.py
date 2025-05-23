import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from ...domain.interfaces.memory import MemoryStore, ContextManager, VectorStore
from ...application.memory.context_manager import InMemoryStore, SimpleContextManager
from ...application.memory.json_file_store import JSONFileStore
from ...application.memory.chromadb_store import ChromaDBStore
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

    def __init__(self, config: Dict[str, Any] = None, memory_store: Optional[MemoryStore] = None,
                 context_manager: Optional[ContextManager] = None,
                 vector_store: Optional[VectorStore] = None,
                 create_paths: bool = True):
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
        self.storage_type = self.config.get("memory_store_type", settings.memory_store_type)
        self.memory_path = self.config.get("memory_file_path", settings.memory_file_path)
        self.max_context_size = self.config.get("max_context_size", settings.max_context_size)
        self.context_expiration_days = self.config.get("context_expiration_days", settings.context_expiration_days)
        self.vector_store_enabled = self.config.get("vector_store_enabled", settings.vector_store_enabled)
        self.chromadb_collection_name = self.config.get("chromadb_collection_name", settings.chromadb_collection_name)

        # Support for direct dependency injection
        self.memory_store = memory_store
        self.context_manager = context_manager
        self.vector_store = vector_store

        # Initialize components only if they weren't injected
        if all(component is None for component in [memory_store, context_manager, vector_store]):
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

            logger.info(f"Memory system initialized with injected components: {', '.join(injected)}")

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
            self.memory_store = JSONFileStore(self.memory_path)
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days
            )
            # No vector store for file-based storage by default
            self.vector_store = None
        elif self.storage_type == "chromadb":
            self.memory_store = ChromaDBStore(self.memory_path)
            self.context_manager = PersistentContextManager(
                self.memory_path,
                max_context_size=self.max_context_size,
                expiration_days=self.context_expiration_days
            )
            # Initialize vector store if enabled
            if self.vector_store_enabled:
                self.vector_store = ChromaDBAdapter(
                    persist_directory=self.memory_path,
                    collection_name=self.chromadb_collection_name
                )
            else:
                self.vector_store = None
        else:
            # Default to in-memory storage
            self.memory_store = InMemoryStore()
            self.context_manager = SimpleContextManager()
            self.vector_store = None

        logger.info(f"Initialized memory system with storage type: {self.storage_type}")
        if self.vector_store:
            logger.info(f"Vector store enabled with ChromaDB collection: {self.chromadb_collection_name}")

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
            "total_tokens": store_tokens + context_tokens
        }

    @classmethod
    def create_for_testing(cls, storage_type: str = "memory", memory_path: Optional[Union[str, Path]] = None) -> "MemorySystemAdapter":
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
            "vector_store_enabled": storage_type == "chromadb"
        }

        if memory_path:
            config["memory_file_path"] = str(memory_path)

        # Create with create_paths=False by default for tests
        # Tests should explicitly create paths if needed
        return cls(config=config, create_paths=False)
