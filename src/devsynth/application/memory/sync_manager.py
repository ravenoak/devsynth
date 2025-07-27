"""Synchronization manager for hybrid memory."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import asyncio
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime

from ...logging_setup import DevSynthLogger
from ...domain.models.memory import MemoryItem
from .tiered_cache import TieredCache

if TYPE_CHECKING:
    from .memory_manager import MemoryManager

logger = DevSynthLogger(__name__)


class SyncManager:
    """Synchronize memory items between different stores."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        cache_size: int = 50,
        *,
        async_mode: bool = False,
    ) -> None:
        self.memory_manager = memory_manager
        self._queue: List[tuple[str, MemoryItem]] = []
        self.cache: TieredCache[Dict[str, List[Any]]] = TieredCache(max_size=cache_size)
        self.conflict_log: List[Dict[str, Any]] = []
        self.stats: Dict[str, int] = {"synchronized": 0, "conflicts": 0}
        self._async_tasks: List[asyncio.Task] = []
        self.async_mode = async_mode

    def _get_all_items(self, adapter: Any) -> List[MemoryItem]:
        if hasattr(adapter, "get_all_items"):
            return adapter.get_all_items()
        if hasattr(adapter, "search"):
            return adapter.search({})
        return []

    def _get_all_vectors(self, adapter: Any) -> List[Any]:
        if hasattr(adapter, "get_all_vectors"):
            return adapter.get_all_vectors()
        return []

    # ------------------------------------------------------------------
    def _detect_conflict(self, existing: MemoryItem, incoming: MemoryItem) -> bool:
        """Return ``True`` if the two items conflict."""

        return (
            existing.content != incoming.content
            or existing.metadata != incoming.metadata
        )

    def _resolve_conflict(
        self, existing: MemoryItem, incoming: MemoryItem
    ) -> MemoryItem:
        """Resolve a conflict by choosing the newest item."""

        winner = incoming if incoming.created_at >= existing.created_at else existing
        self.conflict_log.append(
            {
                "id": existing.id,
                "existing": existing,
                "incoming": incoming,
                "chosen": winner,
                "timestamp": datetime.now(),
            }
        )
        self.stats["conflicts"] += 1
        return winner

    def _copy_item(self, item: MemoryItem) -> MemoryItem:
        return deepcopy(item)

    # ------------------------------------------------------------------
    @contextmanager
    def transaction(self, stores: List[str]):
        """Context manager for multi-store transactions."""

        snapshots: Dict[str, List[MemoryItem]] = {}
        for name in stores:
            adapter = self.memory_manager.adapters.get(name)
            if adapter:
                snapshots[name] = [
                    self._copy_item(i) for i in self._get_all_items(adapter)
                ]
        try:
            yield
        except Exception as exc:  # pragma: no cover - defensive
            for name, items in snapshots.items():
                adapter = self.memory_manager.adapters.get(name)
                if not adapter:
                    continue
                if hasattr(adapter, "delete"):
                    for itm in self._get_all_items(adapter):
                        adapter.delete(itm.id)
                for itm in items:
                    if hasattr(adapter, "store"):
                        adapter.store(itm)
            logger.error("Transaction rolled back due to error: %s", exc)
            raise

    def synchronize(
        self, source: str, target: str, bidirectional: bool = False
    ) -> Dict[str, int]:
        """Synchronize items from source to target (optionally both ways)."""
        source_adapter = self.memory_manager.adapters.get(source)
        target_adapter = self.memory_manager.adapters.get(target)
        if not source_adapter or not target_adapter:
            logger.warning("Sync failed due to missing adapters")
            return {"error": 1}

        count = 0
        for item in self._get_all_items(source_adapter):
            to_store = item
            existing = None
            if hasattr(target_adapter, "retrieve"):
                existing = target_adapter.retrieve(item.id)
            if existing and self._detect_conflict(existing, item):
                to_store = self._resolve_conflict(existing, item)
            if hasattr(target_adapter, "store"):
                target_adapter.store(to_store)
                count += 1
                self.stats["synchronized"] += 1
            if existing and to_store is existing and hasattr(source_adapter, "store"):
                source_adapter.store(existing)

        for vector in self._get_all_vectors(source_adapter):
            existing_vec = None
            if hasattr(target_adapter, "retrieve_vector"):
                existing_vec = target_adapter.retrieve_vector(vector.id)
            if existing_vec is None and hasattr(target_adapter, "store_vector"):
                target_adapter.store_vector(vector)
                count += 1
                self.stats["synchronized"] += 1
        result = {f"{source}_to_{target}": count}

        if bidirectional:
            reverse = self.synchronize(target, source, False)
            result.update(reverse)
        return result

    def update_item(self, store: str, item: MemoryItem) -> bool:
        """Update item in one store and propagate to others."""
        adapter = self.memory_manager.adapters.get(store)
        if not adapter:
            return False
        if hasattr(adapter, "store"):
            adapter.store(item)
        for name, other in self.memory_manager.adapters.items():
            if name == store or not hasattr(other, "store"):
                continue
            existing = None
            if hasattr(other, "retrieve"):
                existing = other.retrieve(item.id)
            to_store = item
            if existing and self._detect_conflict(existing, item):
                to_store = self._resolve_conflict(existing, item)
            other.store(to_store)
            if existing and to_store is existing and hasattr(adapter, "store"):
                adapter.store(existing)
        self.stats["synchronized"] += 1
        return True

    def queue_update(self, store: str, item: MemoryItem) -> None:
        """Queue an update for asynchronous propagation."""
        self._queue.append((store, item))
        if self.async_mode:
            self.schedule_flush()

    def flush_queue(self) -> None:
        """Propagate all queued updates."""
        for store, item in self._queue:
            self.update_item(store, item)
        self._queue = []

    async def flush_queue_async(self) -> None:
        """Asynchronously propagate queued updates."""
        for store, item in self._queue:
            self.update_item(store, item)
            await asyncio.sleep(0)
        self._queue = []

    def schedule_flush(self, delay: float = 0.1) -> None:
        async def _delayed():
            await asyncio.sleep(delay)
            await self.flush_queue_async()

        task = asyncio.create_task(_delayed())
        self._async_tasks.append(task)

    async def wait_for_async(self) -> None:
        if self._async_tasks:
            await asyncio.gather(*self._async_tasks)
            self._async_tasks = []

    def cross_store_query(
        self, query: str, stores: Optional[List[str]] | None = None
    ) -> Dict[str, List[Any]]:
        """Query multiple stores and cache the aggregated results."""

        key_stores = ",".join(sorted(stores)) if stores else "all"
        cache_key = f"{query}:{key_stores}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        stores = stores or list(self.memory_manager.adapters.keys())
        results: Dict[str, List[Any]] = {}
        for name in stores:
            adapter = self.memory_manager.adapters.get(name)
            if not adapter:
                continue
            if name == "vector" and hasattr(adapter, "similarity_search"):
                embedding = self.memory_manager._embed_text(query)
                results[name] = adapter.similarity_search(embedding, top_k=5)
            elif hasattr(adapter, "search"):
                results[name] = adapter.search({"content": query})

        self.cache.put(cache_key, results)
        return results

    def clear_cache(self) -> None:
        """Clear cached query results."""

        self.cache.clear()

    def get_cache_size(self) -> int:
        """Return number of cached queries."""

        return self.cache.size()

    # ------------------------------------------------------------------
    def get_sync_stats(self) -> Dict[str, int]:
        """Return statistics about synchronization operations."""

        return dict(self.stats)
