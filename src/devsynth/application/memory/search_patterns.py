"""High level search helpers for the hybrid memory system."""

from __future__ import annotations

from typing import Any, Dict, List

from .memory_manager import MemoryManager
from .query_router import QueryRouter


class SearchPatterns:
    """Provide convenience methods for common search patterns."""

    def __init__(self, manager: MemoryManager) -> None:
        self.manager = manager
        self.router = QueryRouter(manager)

    def direct_search(self, query: str, store: str) -> List[Any]:
        """Search a single store directly."""
        return self.router.direct_query(query, store)

    def cross_store_search(self, query: str) -> Dict[str, List[Any]]:
        """Search all configured stores and return grouped results."""
        return self.router.cross_store_query(query)

    def federated_search(self, query: str) -> List[Any]:
        """Search all stores and return a ranked, aggregated list."""
        return self.router.federated_query(query)
