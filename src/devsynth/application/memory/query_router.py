"""Query Router for hybrid memory system."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing import TYPE_CHECKING
from ...logging_setup import DevSynthLogger

if TYPE_CHECKING:
    from .memory_manager import MemoryManager

logger = DevSynthLogger(__name__)


class QueryRouter:
    """Route queries to the appropriate memory stores."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory_manager = memory_manager

    def direct_query(self, query: str, store: str) -> List[Any]:
        """Query a single store directly.

        The returned items include a ``source_store`` field in their metadata so
        that callers can trace where each result originated.
        """
        store = store.lower()
        adapter = self.memory_manager.adapters.get(store)
        if not adapter:
            logger.warning("Adapter %s not found", store)
            return []

        if store == "vector":
            results = self.memory_manager.search_memory(query)
            for item in results:
                item.metadata.setdefault("source_store", store)
            return results

        if store == "graph" and not hasattr(adapter, "search"):
            # Use specialized graph query if available
            results = self.memory_manager.query_related_items(query)
            for item in results:
                item.metadata.setdefault("source_store", store)
            return results

        if hasattr(adapter, "search"):
            if isinstance(query, str):
                results = adapter.search({"content": query})
            else:
                results = adapter.search(query)
            for item in results:
                if hasattr(item, "metadata"):
                    item.metadata.setdefault("source_store", store)
                elif isinstance(item, dict):
                    item["source_store"] = store
            return results

        logger.warning("Adapter %s does not support direct queries", store)
        return []

    def cross_store_query(self, query: str) -> Dict[str, List[Any]]:
        """Query all configured stores and return grouped results."""
        grouped = self.memory_manager.sync_manager.cross_store_query(query)
        for store, items in grouped.items():
            for item in items:
                if hasattr(item, "metadata"):
                    item.metadata.setdefault("source_store", store)
                elif isinstance(item, dict):
                    item["source_store"] = store
        return grouped

    def cascading_query(
        self, query: str, order: Optional[List[str]] = None
    ) -> List[Any]:
        """Query stores in sequence and aggregate results."""
        order = order or ["document", "tinydb", "vector", "graph"]
        results: List[Any] = []
        for name in order:
            if name in self.memory_manager.adapters:
                results.extend(self.direct_query(query, name))
        return results

    def federated_query(self, query: str) -> List[Any]:
        """Perform a federated query across all stores.

        This method aggregates results from all stores, removes duplicates by
        ID, and ranks them by simple cosine similarity against the query
        embedding.
        """
        grouped = self.cross_store_query(query)
        aggregated: List[Any] = []
        seen: set[str] = set()
        for items in grouped.values():
            for item in items:
                item_id = getattr(item, "id", id(item))
                if item_id not in seen:
                    seen.add(item_id)
                    aggregated.append(item)

        query_emb = self.memory_manager._embed_text(query)

        def _embed(obj: Any) -> List[float]:
            if hasattr(obj, "embedding"):
                return obj.embedding
            content = getattr(obj, "content", "")
            return self.memory_manager._embed_text(str(content))

        def _similarity(a: List[float], b: List[float]) -> float:
            import math

            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        aggregated.sort(
            key=lambda item: _similarity(query_emb, _embed(item)), reverse=True
        )

        return aggregated

    def context_aware_query(
        self, query: str, context: Dict[str, Any], store: Optional[str] = None
    ) -> Any:
        """Enhance the query with context information."""
        context_str = " ".join(f"{k}:{v}" for k, v in context.items())
        enhanced_query = f"{query} {context_str}".strip()
        if store:
            return self.direct_query(enhanced_query, store)
        return self.cross_store_query(enhanced_query)

    def route(
        self,
        query: str,
        store: Optional[str] = None,
        strategy: str = "direct",
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Route a query according to the specified strategy."""
        if strategy == "direct" and store:
            return self.direct_query(query, store)
        if strategy == "cross":
            return self.cross_store_query(query)
        if strategy == "cascading":
            return self.cascading_query(query)
        if strategy == "federated":
            return self.federated_query(query)
        if strategy == "context_aware":
            return self.context_aware_query(query, context or {}, store)

        logger.warning("Unknown query strategy %s", strategy)
        return []
