from abc import ABC, abstractmethod
from typing import Any, Dict, List


class MemoryStore(ABC):
    """
    Abstract interface for memory storage backends.
    Supports storing, retrieving, and searching artifacts (e.g., code, requirements, embeddings).
    """

    @abstractmethod
    def add(self, item: Dict[str, Any]) -> str:
        """Add an item to the memory store. Returns item ID."""
        raise NotImplementedError("add must be implemented by subclasses")

    @abstractmethod
    def get(self, item_id: str) -> Dict[str, Any]:
        """Retrieve an item by ID."""
        raise NotImplementedError("get must be implemented by subclasses")

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search for items matching the query."""
        raise NotImplementedError("search must be implemented by subclasses")

    @abstractmethod
    def all(self) -> List[Dict[str, Any]]:
        """Return all items in the store."""
        raise NotImplementedError("all must be implemented by subclasses")

    @abstractmethod
    def remove(self, item_id: str) -> None:
        """Remove an item by ID."""
        raise NotImplementedError("remove must be implemented by subclasses")
