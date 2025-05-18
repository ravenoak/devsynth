
import os
from typing import Any, Dict, List, Optional
from ...domain.interfaces.memory import MemoryStore, ContextManager, VectorStore
from ...application.memory.context_manager import InMemoryStore, SimpleContextManager
from ...application.memory.json_file_store import JSONFileStore
from ...application.memory.chromadb_store import ChromaDBStore
from ...application.memory.persistent_context_manager import PersistentContextManager
from ...adapters.memory.chroma_db_adapter import ChromaDBAdapter
from ...config import (
    MEMORY_STORE_TYPE, 
    MEMORY_FILE_PATH, 
    MAX_CONTEXT_SIZE, 
    CONTEXT_EXPIRATION_DAYS,
    VECTOR_STORE_ENABLED,
    CHROMADB_COLLECTION_NAME
)

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class MemorySystemAdapter:
    """Adapter for the memory system."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the memory system adapter.

        Args:
            config: Optional configuration dictionary that overrides environment variables
        """
        self.config = config or {}

        # Determine storage type from config or environment
        storage_type = self.config.get("memory_store_type", MEMORY_STORE_TYPE)
        memory_path = self.config.get("memory_file_path", MEMORY_FILE_PATH)
        max_context_size = self.config.get("max_context_size", MAX_CONTEXT_SIZE)
        context_expiration_days = self.config.get("context_expiration_days", CONTEXT_EXPIRATION_DAYS)
        vector_store_enabled = self.config.get("vector_store_enabled", VECTOR_STORE_ENABLED)
        chromadb_collection_name = self.config.get("chromadb_collection_name", CHROMADB_COLLECTION_NAME)

        # Ensure the memory directory exists
        if storage_type in ["file", "chromadb"]:
            os.makedirs(memory_path, exist_ok=True)

        # Initialize the appropriate store and context manager
        if storage_type == "file":
            self.memory_store = JSONFileStore(memory_path)
            self.context_manager = PersistentContextManager(
                memory_path, 
                max_context_size=max_context_size,
                expiration_days=context_expiration_days
            )
            # No vector store for file-based storage by default
            self.vector_store = None
        elif storage_type == "chromadb":
            self.memory_store = ChromaDBStore(memory_path)
            self.context_manager = PersistentContextManager(
                memory_path, 
                max_context_size=max_context_size,
                expiration_days=context_expiration_days
            )
            # Initialize vector store if enabled
            if vector_store_enabled:
                self.vector_store = ChromaDBAdapter(
                    persist_directory=memory_path,
                    collection_name=chromadb_collection_name
                )
            else:
                self.vector_store = None
        else:
            # Default to in-memory storage
            self.memory_store = InMemoryStore()
            self.context_manager = SimpleContextManager()
            self.vector_store = None

        logger.info(f"Initialized memory system with storage type: {storage_type}")
        if self.vector_store:
            logger.info(f"Vector store enabled with ChromaDB collection: {chromadb_collection_name}")

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
