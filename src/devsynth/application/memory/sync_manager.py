"""Synchronization manager for hybrid memory."""

from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from threading import Lock, RLock
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

try:  # pragma: no cover - optional dependencies
    from .lmdb_store import LMDBStore
except Exception:  # pragma: no cover - optional dependency
    LMDBStore = None
try:  # pragma: no cover - optional dependencies
    from .faiss_store import FAISSStore
except Exception:  # pragma: no cover - optional dependency
    FAISSStore = None
try:  # pragma: no cover - optional dependencies
    from ...adapters.kuzu_memory_store import KuzuMemoryStore
except Exception:  # pragma: no cover - optional dependency
    KuzuMemoryStore = None

from ...domain.models.memory import MemoryItem
from ...logging_setup import DevSynthLogger
from .tiered_cache import TieredCache

if TYPE_CHECKING:
    from .memory_manager import MemoryManager


class DummyTransactionContext:
    """
    A dummy transaction context for adapters that have begin_transaction
    but don't return a context manager.
    """

    def __init__(self, adapter: Any, transaction_id: str = None):
        self.adapter = adapter
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        """Begin the transaction."""
        if hasattr(self.adapter, "begin_transaction"):
            begin = getattr(self.adapter, "begin_transaction")
            try:
                if "transaction_id" in begin.__code__.co_varnames:
                    result = begin(self.transaction_id)
                else:
                    result = begin()
            except TypeError:
                result = begin()

            # If begin_transaction returns a context manager, use it
            if hasattr(result, "__enter__") and hasattr(result, "__exit__"):
                self.context = result
                return self.context.__enter__()
            # Otherwise, just return the result
            return result
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Commit or roll back the transaction."""
        if hasattr(self, "context"):
            return self.context.__exit__(exc_type, exc_val, exc_tb)

        if exc_type is None:
            # Commit the transaction
            if hasattr(self.adapter, "commit_transaction"):
                self.adapter.commit_transaction(self.transaction_id)
                self.committed = True
        else:
            # Roll back the transaction
            if hasattr(self.adapter, "rollback_transaction"):
                self.adapter.rollback_transaction(self.transaction_id)
                self.rolled_back = True
        return False  # Don't suppress exceptions


logger = DevSynthLogger(__name__)


class LMDBTransactionContext:
    """Transaction context for :class:`LMDBStore`."""

    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter
        self._context = None

    def __enter__(self):
        ctx = self.adapter.begin_transaction()
        if hasattr(ctx, "__enter__"):
            self._context = ctx
            return ctx.__enter__()
        self._context = None
        return ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context and hasattr(self._context, "__exit__"):
            return self._context.__exit__(exc_type, exc_val, exc_tb)
        return False


class FAISSTransactionContext:
    """Snapshot-based transaction context for :class:`FAISSStore`."""

    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter
        self._snapshot: Dict[str, Any] = {}

    def __enter__(self):
        vectors = (
            self.adapter.get_all_vectors()
            if hasattr(self.adapter, "get_all_vectors")
            else []
        )
        self._snapshot = {v.id: deepcopy(v) for v in vectors}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            current = (
                self.adapter.get_all_vectors()
                if hasattr(self.adapter, "get_all_vectors")
                else []
            )
            current_ids = {v.id for v in current}
            snap_ids = set(self._snapshot.keys())
            for vid in current_ids - snap_ids:
                if hasattr(self.adapter, "delete_vector"):
                    self.adapter.delete_vector(vid)
            for vec in self._snapshot.values():
                if hasattr(self.adapter, "store_vector"):
                    self.adapter.store_vector(vec)
        return False


class KuzuTransactionContext:
    """Snapshot-based transaction context for :class:`KuzuMemoryStore`."""

    def __init__(self, adapter: Any) -> None:
        self.adapter = adapter
        self._items: Dict[str, MemoryItem] = {}
        self._vectors: Dict[str, Any] = {}

    def __enter__(self):
        items = (
            self.adapter.get_all_items()
            if hasattr(self.adapter, "get_all_items")
            else []
        )
        vectors = (
            self.adapter.get_all_vectors()
            if hasattr(self.adapter, "get_all_vectors")
            else []
        )
        self._items = {i.id: deepcopy(i) for i in items}
        self._vectors = {v.id: deepcopy(v) for v in vectors}
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            current_items = (
                self.adapter.get_all_items()
                if hasattr(self.adapter, "get_all_items")
                else []
            )
            current_ids = {i.id for i in current_items}
            snap_ids = set(self._items.keys())
            for item_id in current_ids - snap_ids:
                if hasattr(self.adapter, "delete"):
                    self.adapter.delete(item_id)
            for item in self._items.values():
                if hasattr(self.adapter, "store"):
                    self.adapter.store(item)
            current_vectors = (
                self.adapter.get_all_vectors()
                if hasattr(self.adapter, "get_all_vectors")
                else []
            )
            current_vec_ids = {v.id for v in current_vectors}
            snap_vec_ids = set(self._vectors.keys())
            for vec_id in current_vec_ids - snap_vec_ids:
                if hasattr(self.adapter, "delete_vector"):
                    self.adapter.delete_vector(vec_id)
            for vec in self._vectors.values():
                if hasattr(self.adapter, "store_vector"):
                    self.adapter.store_vector(vec)
        return False


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
        self._queue_lock = Lock()
        self.cache: TieredCache[Dict[str, List[Any]]] = TieredCache(max_size=cache_size)
        self.conflict_log: List[Dict[str, Any]] = []
        self.stats: Dict[str, int] = {"synchronized": 0, "conflicts": 0}
        self._async_tasks: List[asyncio.Task] = []
        self.async_mode = async_mode
        # Dictionary to store active transactions
        self._active_transactions: Dict[str, Dict[str, Any]] = {}

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

    def _get_transaction_context(self, adapter: Any, transaction_id: str):
        """Return an adapter-specific transaction context if supported."""

        if LMDBStore and isinstance(adapter, LMDBStore):
            return LMDBTransactionContext(adapter)
        if FAISSStore and isinstance(adapter, FAISSStore):
            return FAISSTransactionContext(adapter)
        if KuzuMemoryStore and isinstance(adapter, KuzuMemoryStore):
            return KuzuTransactionContext(adapter)
        if hasattr(adapter, "begin_transaction") or hasattr(adapter, "transaction"):
            return DummyTransactionContext(adapter, transaction_id)
        return None

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
        """Context manager for multi-store transactions.

        This manager attempts to use native transaction support on each
        adapter if available and falls back to snapshot/restore semantics
        otherwise. All changes are rolled back if an exception occurs.

        Args:
            stores: List of store names to include in the transaction

        Yields:
            Dictionary mapping store names to transaction objects

        Raises:
            Exception: If any error occurs during the transaction
        """
        transaction_id = str(uuid.uuid4())
        logger.debug(f"Starting transaction {transaction_id} for stores: {stores}")

        snapshots: Dict[str, Dict[str, Dict[str, Any]]] = {}
        contexts: Dict[str, Any] = {}
        txns: Dict[str, Any] = {}
        added_items: Dict[str, Set[str]] = {}

        # Track which stores are participating in the transaction
        participating_stores = []

        # Begin transaction for each store
        for name in stores:
            adapter = self.memory_manager.adapters.get(name)
            if not adapter:
                logger.warning(f"Store {name} not found, skipping")
                continue

            participating_stores.append(name)
            added_items[name] = set()

            try:
                ctx = self._get_transaction_context(adapter, transaction_id)
                if ctx is not None:
                    txns[name] = ctx.__enter__()
                    contexts[name] = ctx
                else:
                    items = self._get_all_items(adapter)
                    vectors = self._get_all_vectors(adapter)
                    snapshots[name] = {
                        "items": {item.id: self._copy_item(item) for item in items},
                        "vectors": {vec.id: deepcopy(vec) for vec in vectors},
                    }
                    logger.debug(
                        f"Created snapshot for {name} with {len(snapshots[name]['items'])} items and {len(snapshots[name]['vectors'])} vectors"
                    )
            except Exception as e:
                logger.error(f"Error beginning transaction for {name}: {e}")
                # Roll back any stores that were already set up
                self._rollback_partial_transaction(contexts, snapshots, added_items)
                raise

        try:
            # Yield the transaction objects to the caller
            yield txns

            # If we get here, commit all transactions
            for name, ctx in contexts.items():
                try:
                    ctx.__exit__(None, None, None)
                    logger.debug(f"Committed transaction for {name}")
                except Exception as e:
                    logger.error(f"Error committing transaction for {name}: {e}")
                    # If a commit fails, we need to roll back all stores
                    self._rollback_partial_transaction(contexts, snapshots, added_items)
                    raise

            logger.debug(f"Transaction {transaction_id} committed successfully")

        except Exception as exc:
            # Roll back all transactions
            logger.error(f"Transaction {transaction_id} failed: {exc}")
            self._rollback_partial_transaction(contexts, snapshots, added_items, exc)
            raise

    def _rollback_partial_transaction(
        self,
        contexts: Dict[str, Any],
        snapshots: Dict[str, Dict[str, Dict[str, Any]]],
        added_items: Dict[str, Set[str]],
        exc: Exception = None,
    ):
        """
        Roll back a partially completed transaction.

        Args:
            contexts: Dictionary mapping store names to transaction contexts
            snapshots: Dictionary mapping store names to snapshots
            added_items: Dictionary mapping store names to sets of added item IDs
            exc: Exception that caused the rollback, if any
        """
        rollback_errors = []

        # Create a dummy exception if none was provided
        if exc is None:
            exc = ValueError("Transaction rolled back")

        # Roll back stores with native transaction support
        for name, ctx in contexts.items():
            try:
                ctx.__exit__(type(exc), exc, exc.__traceback__)
                logger.debug(f"Rolled back transaction for {name}")
            except Exception as e:
                error_msg = f"Error rolling back transaction for {name}: {e}"
                logger.error(error_msg)
                rollback_errors.append(error_msg)

        # Restore snapshots for stores without native transaction support
        for name, snap in snapshots.items():
            adapter = self.memory_manager.adapters.get(name)
            if not adapter:
                continue

            try:
                items = snap.get("items", {})
                vectors = snap.get("vectors", {})

                current_items = self._get_all_items(adapter)
                current_ids = {item.id for item in current_items}
                for item_id in current_ids - set(items.keys()):
                    if hasattr(adapter, "delete"):
                        adapter.delete(item_id)
                        logger.debug(f"Deleted added item {item_id} from {name}")
                for item_id, item in items.items():
                    if hasattr(adapter, "store"):
                        adapter.store(item)
                        logger.debug(f"Restored item {item_id} in {name}")

                current_vectors = self._get_all_vectors(adapter)
                current_vec_ids = {vec.id for vec in current_vectors}
                for vec_id in current_vec_ids - set(vectors.keys()):
                    if hasattr(adapter, "delete_vector"):
                        adapter.delete_vector(vec_id)
                        logger.debug(f"Deleted added vector {vec_id} from {name}")
                for vec_id, vec in vectors.items():
                    if hasattr(adapter, "store_vector"):
                        adapter.store_vector(vec)
                        logger.debug(f"Restored vector {vec_id} in {name}")

                logger.debug(f"Restored snapshot for {name}")
            except Exception as e:
                error_msg = f"Error restoring snapshot for {name}: {e}"
                logger.error(error_msg)
                rollback_errors.append(error_msg)

        # If there were errors during rollback, log them but don't raise
        # (we want to continue with the original exception)
        if rollback_errors:
            logger.error(f"Errors during transaction rollback: {rollback_errors}")

        logger.error(f"Transaction rolled back due to error: {exc}")

    def _sync_one_way(self, source_adapter: Any, target_adapter: Any) -> int:
        """Synchronize data from ``source_adapter`` to ``target_adapter``.

        This helper performs a one-way sync of both memory items and vectors,
        applying the conflict resolution strategy where necessary.

        Args:
            source_adapter: Adapter providing the items/vectors to copy
            target_adapter: Adapter receiving the synchronized data

        Returns:
            int: Number of items/vectors synchronized
        """

        count = 0

        # Synchronize memory items
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

        # Synchronize vectors
        for vector in self._get_all_vectors(source_adapter):
            existing_vec = None
            if hasattr(target_adapter, "retrieve_vector"):
                existing_vec = target_adapter.retrieve_vector(vector.id)
            if existing_vec is None and hasattr(target_adapter, "store_vector"):
                target_adapter.store_vector(vector)
                count += 1
                self.stats["synchronized"] += 1

        return count

    def synchronize(
        self, source: str, target: str, bidirectional: bool = False
    ) -> Dict[str, int]:
        """Synchronize items from ``source`` to ``target`` transactionally.

        If ``bidirectional`` is ``True``, the reverse synchronization is
        performed within the same transaction to ensure atomicity across both
        directions.
        """

        source_adapter = self.memory_manager.adapters.get(source)
        target_adapter = self.memory_manager.adapters.get(target)
        if not source_adapter or not target_adapter:
            logger.warning(
                "Sync skipped due to missing adapters: %s -> %s", source, target
            )
            return {f"{source}_to_{target}": 0}

        result: Dict[str, int] = {}

        # Execute synchronization inside a transaction for atomicity
        with self.transaction([source, target]):
            forward = self._sync_one_way(source_adapter, target_adapter)
            result[f"{source}_to_{target}"] = forward
            if bidirectional:
                reverse = self._sync_one_way(target_adapter, source_adapter)
                result[f"{target}_to_{source}"] = reverse
        try:
            self.memory_manager._notify_sync_hooks(None)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)
        return result

    def synchronize_core(self) -> Dict[str, int]:
        """Synchronize LMDB and FAISS stores into the Kuzu store.

        This helper coordinates synchronization across the primary persistent
        backends used by the memory system. If any of the stores are missing
        the operation is skipped for that pair. The method returns a mapping of
        performed synchronization directions to the number of items synced.

        Returns:
            Mapping of synchronization directions to counts.
        """

        results: Dict[str, int] = {}
        adapters = self.memory_manager.adapters

        # Ensure Kuzu is available as the central store
        if "kuzu" not in adapters:
            return results

        stores: List[str] = ["kuzu"]
        if "lmdb" in adapters:
            stores.append("lmdb")
        if "faiss" in adapters:
            stores.append("faiss")

        with self.transaction(stores):
            if "lmdb" in adapters:
                forward = self._sync_one_way(adapters["lmdb"], adapters["kuzu"])
                results["lmdb_to_kuzu"] = forward
            if "faiss" in adapters:
                forward = self._sync_one_way(adapters["faiss"], adapters["kuzu"])
                results["faiss_to_kuzu"] = forward

        try:
            self.memory_manager._notify_sync_hooks(None)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Peer review failed: %s", exc)

        return results

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
        try:
            self.memory_manager._notify_sync_hooks(item)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)
        return True

    def queue_update(self, store: str, item: MemoryItem) -> None:
        """Queue an update for asynchronous propagation."""
        with self._queue_lock:
            self._queue.append((store, item))
        if self.async_mode:
            self.schedule_flush()
        try:
            self.memory_manager._notify_sync_hooks(item)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)

    def flush_queue(self) -> None:
        """Propagate all queued updates."""
        while True:
            with self._queue_lock:
                if not self._queue:
                    break
                store, item = self._queue.pop(0)
            self.update_item(store, item)
        with self._queue_lock:
            self._queue = []
        try:
            self.memory_manager._notify_sync_hooks(None)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)

    async def flush_queue_async(self) -> None:
        """Asynchronously propagate queued updates."""
        while True:
            with self._queue_lock:
                if not self._queue:
                    break
                store, item = self._queue.pop(0)
            self.update_item(store, item)
            await asyncio.sleep(0)
        with self._queue_lock:
            self._queue = []
        try:
            self.memory_manager._notify_sync_hooks(None)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)

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

    async def cross_store_query_async(
        self, query: str, stores: Optional[List[str]] | None = None
    ) -> Dict[str, List[Any]]:
        """Asynchronously query multiple stores and cache the results."""

        key_stores = ",".join(sorted(stores)) if stores else "all"
        cache_key = f"{query}:{key_stores}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        stores = stores or list(self.memory_manager.adapters.keys())

        async def _query(name: str) -> Tuple[str, List[Any]]:
            adapter = self.memory_manager.adapters.get(name)
            if not adapter:
                return name, []
            if name == "vector" and hasattr(adapter, "similarity_search"):
                embedding = self.memory_manager._embed_text(query)
                result = await asyncio.to_thread(
                    adapter.similarity_search, embedding, top_k=5
                )
                return name, result
            if hasattr(adapter, "search"):
                result = await asyncio.to_thread(adapter.search, {"content": query})
                return name, result
            return name, []

        pairs = await asyncio.gather(*(_query(name) for name in stores))
        results: Dict[str, List[Any]] = {name: items for name, items in pairs}
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

    # ------------------------------------------------------------------
    # Explicit transaction methods to support peer review workflow

    def begin_transaction(self, transaction_id: str | None = None) -> str:
        """
        Begin a new transaction and return its identifier.

        The transaction ID may be supplied by the caller or generated
        automatically. This method starts a transaction that can later be
        committed or rolled back via :meth:`commit_transaction` or
        :meth:`rollback_transaction`.

        Args:
            transaction_id: Optional unique identifier for the transaction

        Returns:
            str: The transaction identifier
        """
        tx_id = transaction_id or str(uuid.uuid4())
        if tx_id in self._active_transactions:
            logger.warning(f"Transaction {tx_id} already exists")
            return tx_id

        logger.debug(f"Beginning transaction {tx_id}")

        # Get all store names
        stores = list(self.memory_manager.adapters.keys())

        # Initialize transaction state
        snapshots: Dict[str, Dict[str, List[Any]]] = {}
        contexts = {}
        txns = {}

        # Begin transaction for each store
        for name in stores:
            adapter = self.memory_manager.adapters.get(name)
            if not adapter:
                continue
            if hasattr(adapter, "begin_transaction"):
                ctx = DummyTransactionContext(adapter, tx_id)
                txns[name] = ctx.__enter__()
                contexts[name] = ctx
            else:
                snapshots[name] = {
                    "items": [self._copy_item(i) for i in self._get_all_items(adapter)],
                    "vectors": [deepcopy(v) for v in self._get_all_vectors(adapter)],
                }

        # Store transaction state
        self._active_transactions[tx_id] = {
            "stores": stores,
            "snapshots": snapshots,
            "contexts": contexts,
            "txns": txns,
            "started_at": datetime.now(),
        }

        return tx_id

    def commit_transaction(self, transaction_id: str) -> None:
        """
        Commit the transaction with the given ID.

        This method commits a previously started transaction, making all changes permanent.

        Args:
            transaction_id: The unique identifier for the transaction

        Raises:
            ValueError: If no transaction with the given ID exists
        """
        if transaction_id not in self._active_transactions:
            logger.warning(f"No transaction {transaction_id} to commit")
            return

        logger.debug(f"Committing transaction {transaction_id}")

        # Get transaction state
        transaction = self._active_transactions[transaction_id]
        contexts = transaction.get("contexts", {})

        # Commit transaction for each store
        for ctx in contexts.values():
            ctx.__exit__(None, None, None)

        # Flush any queued updates to ensure persistence across stores
        try:
            self.flush_queue()
            if self.async_mode:
                asyncio.run(self.wait_for_async())
        except Exception as e:
            logger.error(
                f"Error flushing updates for transaction {transaction_id}: {e}"
            )

        # Remove transaction state
        del self._active_transactions[transaction_id]

    def rollback_transaction(self, transaction_id: str) -> None:
        """
        Roll back the transaction with the given ID.

        This method rolls back a previously started transaction, discarding all changes.

        Args:
            transaction_id: The unique identifier for the transaction

        Raises:
            ValueError: If no transaction with the given ID exists
        """
        if transaction_id not in self._active_transactions:
            logger.warning(f"No transaction {transaction_id} to roll back")
            return

        logger.debug(f"Rolling back transaction {transaction_id}")

        # Get transaction state
        transaction = self._active_transactions[transaction_id]
        contexts = transaction.get("contexts", {})
        snapshots = transaction.get("snapshots", {})

        # Create a dummy exception for rollback
        exc = ValueError("Transaction rolled back")

        # Roll back transaction for each store
        for ctx in contexts.values():
            ctx.__exit__(type(exc), exc, exc.__traceback__)

        # Restore snapshots for stores without native transaction support
        for name, snap in snapshots.items():
            adapter = self.memory_manager.adapters.get(name)
            if not adapter:
                continue
            items = snap.get("items", [])
            vectors = snap.get("vectors", [])
            if hasattr(adapter, "delete"):
                for itm in self._get_all_items(adapter):
                    adapter.delete(itm.id)
            if hasattr(adapter, "delete_vector"):
                for vec in self._get_all_vectors(adapter):
                    adapter.delete_vector(vec.id)
            for itm in items:
                if hasattr(adapter, "store"):
                    adapter.store(itm)
            for vec in vectors:
                if hasattr(adapter, "store_vector"):
                    adapter.store_vector(vec)

        # Remove transaction state
        del self._active_transactions[transaction_id]
        # Clear any queued updates that shouldn't be applied
        with self._queue_lock:
            self._queue = []
