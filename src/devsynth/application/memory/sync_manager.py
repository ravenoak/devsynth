"""Synchronization manager for hybrid memory."""

from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

from ...logging_setup import DevSynthLogger
from ...domain.models.memory import MemoryItem

if TYPE_CHECKING:
    from .memory_manager import MemoryManager

logger = DevSynthLogger(__name__)


class SyncManager:
    """Synchronize memory items between different stores."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.memory_manager = memory_manager
        self._queue: List[tuple[str, MemoryItem]] = []

    def _get_all_items(self, adapter: Any) -> List[MemoryItem]:
        if hasattr(adapter, "get_all_items"):
            return adapter.get_all_items()
        if hasattr(adapter, "search"):
            return adapter.search({})
        return []

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
            if hasattr(target_adapter, "store"):
                target_adapter.store(item)
                count += 1
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
            if name != store and hasattr(other, "store"):
                other.store(item)
        return True

    def queue_update(self, store: str, item: MemoryItem) -> None:
        """Queue an update for asynchronous propagation."""
        self._queue.append((store, item))

    def flush_queue(self) -> None:
        """Propagate all queued updates."""
        for store, item in self._queue:
            self.update_item(store, item)
        self._queue = []
