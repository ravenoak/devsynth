"""High level search helpers for the hybrid memory system."""

from __future__ import annotations

from typing import List

from .dto import GroupedMemoryResults, MemoryQueryResults, MemoryRecord
from .memory_manager import MemoryManager
from .query_router import QueryRouter


class SearchPatterns:
    """Provide convenience methods for common search patterns returning DTOs."""

    def __init__(self, manager: MemoryManager) -> None:
        self.manager = manager
        self.router = QueryRouter(manager)

    def direct_search(self, query: str, store: str) -> MemoryQueryResults:
        """Search a single store directly and return normalized results."""

        return self.router.direct_query(query, store)

    def cross_store_search(self, query: str) -> GroupedMemoryResults:
        """Search all configured stores and return grouped DTO responses."""

        return self.router.cross_store_query(query)

    def federated_search(self, query: str) -> list[MemoryRecord]:
        """Search all stores and return a ranked, aggregated list of records."""

        return self.router.federated_query(query)
