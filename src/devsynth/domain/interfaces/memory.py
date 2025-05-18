
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector
from ...domain.models.wsde import WSDE

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class MemoryStore(Protocol):
    """Protocol for memory storage."""
    
    @abstractmethod
    def store(self, item: MemoryItem) -> str:
        """Store an item in memory and return its ID."""
        ...
    
    @abstractmethod
    def retrieve(self, item_id: str) -> Optional[MemoryItem]:
        """Retrieve an item from memory by ID."""
        ...
    
    @abstractmethod
    def search(self, query: Dict[str, Any]) -> List[MemoryItem]:
        """Search for items in memory matching the query."""
        ...
    
    @abstractmethod
    def delete(self, item_id: str) -> bool:
        """Delete an item from memory."""
        ...

class VectorStore(Protocol):
    """Protocol for vector storage."""
    
    @abstractmethod
    def store_vector(self, vector: MemoryVector) -> str:
        """Store a vector in the vector store and return its ID."""
        ...
    
    @abstractmethod
    def retrieve_vector(self, vector_id: str) -> Optional[MemoryVector]:
        """Retrieve a vector from the vector store by ID."""
        ...
    
    @abstractmethod
    def similarity_search(self, query_embedding: List[float], top_k: int = 5) -> List[MemoryVector]:
        """Search for vectors similar to the query embedding."""
        ...
    
    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector from the vector store."""
        ...
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        ...

class ContextManager(Protocol):
    """Protocol for managing context."""
    
    @abstractmethod
    def add_to_context(self, key: str, value: Any) -> None:
        """Add a value to the current context."""
        ...
    
    @abstractmethod
    def get_from_context(self, key: str) -> Optional[Any]:
        """Get a value from the current context."""
        ...
    
    @abstractmethod
    def get_full_context(self) -> Dict[str, Any]:
        """Get the full current context."""
        ...
    
    @abstractmethod
    def clear_context(self) -> None:
        """Clear the current context."""
        ...
