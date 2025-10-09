"""Synchronization manager for hybrid memory.

This module coordinates synchronization across heterogeneous memory stores while
normalizing payloads into the DTOs defined under ``devsynth.application.memory``.
All cross-store exchanges rely on :class:`~devsynth.application.memory.dto.MemoryRecord`
entries so metadata is merged predictably, cache entries remain coherent, and
transaction rollbacks can restore consistent snapshots.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from types import TracebackType
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

try:  # pragma: no cover - optional dependencies
    from .lmdb_store import LMDBStore as LMDBStoreRuntime
except Exception:  # pragma: no cover - optional dependency
    LMDBStoreRuntime = None

from ...domain.models.memory import MemoryItem, MemoryVector
from ...logging_setup import DevSynthLogger
from .adapter_types import AdapterRegistry, MemoryAdapter, SupportsSearch
from .dto import (
    GroupedMemoryResults,
    MemoryQueryResults,
    MemoryRecord,
    MemoryRecordInput,
    build_memory_record,
)
from .tiered_cache import TieredCache
from .transaction_context import AdapterSnapshot
from .vector_protocol import VectorStoreProtocol

if TYPE_CHECKING:
    from .lmdb_store import LMDBStore as LMDBStoreType
    from .memory_manager import MemoryManager
else:
    LMDBStoreType = object


class TransactionContextProtocol(Protocol):
    """Protocol representing transaction context managers."""

    def __enter__(self) -> object:  # pragma: no cover - protocol
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:  # pragma: no cover - protocol
        ...


TransactionContextManager = TransactionContextProtocol


class QueuedUpdate(TypedDict):
    """Structured payload for queued synchronization work."""

    store: str
    record: MemoryRecord
    transaction_id: str | None


class ConflictRecord(TypedDict):
    """Normalized entry describing a conflict resolution decision."""

    id: str
    existing: MemoryItem
    incoming: MemoryItem
    chosen: MemoryItem
    timestamp: datetime


@dataclass(slots=True)
class SyncStats:
    """Summary counters for synchronization activity."""

    synchronized: int = 0
    conflicts: int = 0

    def as_dict(self) -> dict[str, int]:
        return {"synchronized": self.synchronized, "conflicts": self.conflicts}


@dataclass(slots=True)
class TransactionState:
    """Internal bookkeeping for active transactions."""

    stores: list[str]
    snapshots: dict[str, AdapterSnapshot]
    vector_snapshots: dict[str, dict[str, MemoryVector]]
    contexts: dict[str, TransactionContextManager]
    txns: dict[str, object]
    started_at: datetime


class DummyTransactionContext(AbstractContextManager[object]):
    """
    A dummy transaction context for adapters that have begin_transaction
    but don't return a context manager.
    """

    def __init__(
        self, adapter: MemoryAdapter, transaction_id: str | None = None
    ) -> None:
        self.adapter = adapter
        self.transaction_id: str = transaction_id or str(uuid.uuid4())
        self.committed = False
        self.rolled_back = False
        self.context: TransactionContextProtocol | None = None

    def __enter__(self) -> object:
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
                self.context = cast(TransactionContextProtocol, result)
                return self.context.__enter__()
            # Otherwise, just return the result
            return result
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Commit or roll back the transaction."""
        if self.context is not None:
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


class LMDBTransactionContext(AbstractContextManager[object]):
    """Transaction context for :class:`LMDBStore`."""

    def __init__(self, adapter: "LMDBStoreType") -> None:
        self.adapter = adapter
        self._context: TransactionContextProtocol | None = None

    def __enter__(self) -> object:
        ctx = self.adapter.transaction()
        self._context = cast(TransactionContextProtocol, ctx)
        return self._context.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if self._context is not None:
            return self._context.__exit__(exc_type, exc_val, exc_tb)
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
        self._queue: list[QueuedUpdate] = []
        self._queue_lock = Lock()
        self.cache: TieredCache[GroupedMemoryResults] = TieredCache(max_size=cache_size)
        self.conflict_log: list[ConflictRecord] = []
        self.stats = SyncStats()
        self._async_tasks: list[asyncio.Task[None]] = []
        self.async_mode = async_mode
        # Dictionary to store active transactions
        self._active_transactions: dict[str, TransactionState] = {}

    def _get_all_items(
        self, adapter: MemoryAdapter, *, store_name: str
    ) -> list[MemoryItem]:
        if hasattr(adapter, "get_all_items"):
            items = adapter.get_all_items()
            return list(items)
        if hasattr(adapter, "search"):
            results = adapter.search({})
            if isinstance(results, list):
                return [
                    build_memory_record(candidate, source=store_name).item
                    for candidate in results
                ]
            if isinstance(results, dict):
                collected: list[MemoryItem] = []
                records = results.get("records") or results.get("combined")
                if isinstance(records, Sequence):
                    for candidate in records:
                        collected.append(
                            build_memory_record(candidate, source=store_name).item
                        )
                return collected
        return []

    def _get_all_vectors(self, adapter: MemoryAdapter) -> list[MemoryVector]:
        if hasattr(adapter, "get_all_vectors"):
            vectors = adapter.get_all_vectors()
            return list(vectors)
        return []

    def _get_transaction_context(
        self, adapter: MemoryAdapter, transaction_id: str
    ) -> TransactionContextManager | None:
        """Return an adapter-specific transaction context if supported."""

        if LMDBStoreRuntime is not None and isinstance(adapter, LMDBStoreRuntime):
            return LMDBTransactionContext(cast(LMDBStoreType, adapter))
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

        existing_created = existing.created_at or datetime.min
        incoming_created = incoming.created_at or datetime.min
        winner = incoming if incoming_created >= existing_created else existing
        record: ConflictRecord = {
            "id": existing.id,
            "existing": existing,
            "incoming": incoming,
            "chosen": winner,
            "timestamp": datetime.now(),
        }
        self.conflict_log.append(record)
        self.stats.conflicts += 1
        return winner

    def _copy_item(self, item: MemoryItem) -> MemoryItem:
        return deepcopy(item)

    # ------------------------------------------------------------------
    def _adapter_label(self, adapter: MemoryAdapter, default: str) -> str:
        """Return a human readable label for ``adapter``.

        Adapters may expose a ``name`` attribute.  When absent we fall back to
        ``default`` which typically reflects the store key used by
        :class:`MemoryManager`.
        """

        label = getattr(adapter, "name", None)
        if isinstance(label, str) and label:
            return label
        return default

    def _build_record(self, payload: MemoryRecordInput, *, source: str) -> MemoryRecord:
        """Coerce ``payload`` into a :class:`MemoryRecord` for ``source``.

        The helper wraps the :func:`build_memory_record` adapter to ensure
        metadata normalization happens consistently whenever records leave an
        adapter boundary.
        """

        record = build_memory_record(payload, source=source)
        if not record.item.id:
            # Ensure deterministic identifiers even if an adapter omitted one.
            record.item.id = str(uuid.uuid4())
        return record

    def _normalize_records(
        self, payloads: Iterable[MemoryRecordInput], *, source: str
    ) -> list[MemoryRecord]:
        """Return a list of normalized :class:`MemoryRecord` objects."""

        return [self._build_record(payload, source=source) for payload in payloads]

    # ------------------------------------------------------------------
    @contextmanager
    def transaction(self, stores: list[str]) -> Iterator[dict[str, object]]:
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

        snapshots: dict[str, AdapterSnapshot] = {}
        vector_snapshots: dict[str, dict[str, MemoryVector]] = {}
        contexts: dict[str, TransactionContextManager] = {}
        txns: dict[str, object] = {}

        # Track which stores are participating in the transaction
        participating_stores: list[str] = []

        # Begin transaction for each store
        for name in stores:
            adapter = self.memory_manager.adapters.get(name)
            if adapter is None:
                logger.warning(f"Store {name} not found, skipping")
                continue

            participating_stores.append(name)

            try:
                ctx = self._get_transaction_context(adapter, transaction_id)
                if ctx is not None:
                    txns[name] = ctx.__enter__()
                    contexts[name] = ctx
                else:
                    items = self._get_all_items(adapter, store_name=name)
                    vectors = self._get_all_vectors(adapter)
                    normalized = self._normalize_records(items, source=name)
                    snapshots[name] = {
                        "store": name,
                        "records": {record.id: record for record in normalized},
                    }
                    if vectors:
                        vector_snapshots[name] = {
                            vec.id: deepcopy(vec) for vec in vectors
                        }
                    logger.debug(
                        "Created snapshot for %s with %d items and %d vectors",
                        name,
                        len(snapshots[name]["records"]),
                        len(vector_snapshots.get(name, {})),
                    )
            except Exception as e:
                logger.error(f"Error beginning transaction for {name}: {e}")
                # Roll back any stores that were already set up
                self._rollback_partial_transaction(
                    contexts, snapshots, vector_snapshots
                )
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
                    self._rollback_partial_transaction(
                        contexts, snapshots, vector_snapshots
                    )
                    raise

            logger.debug(f"Transaction {transaction_id} committed successfully")

            # Ensure all changes are persisted across stores
            try:
                self.flush_queue()
                if self.async_mode:
                    asyncio.run(self.wait_for_async())
                self.memory_manager.flush_updates()
            except Exception as e:  # pragma: no cover - defensive
                logger.error(
                    f"Error flushing updates for transaction {transaction_id}: {e}"
                )
            # Cached queries may now be stale
            self.clear_cache()

        except Exception as exc:
            # Roll back all transactions
            logger.error(f"Transaction {transaction_id} failed: {exc}")
            self._rollback_partial_transaction(
                contexts, snapshots, vector_snapshots, exc
            )
            raise

    def _rollback_partial_transaction(
        self,
        contexts: dict[str, TransactionContextManager],
        snapshots: dict[str, AdapterSnapshot],
        vector_snapshots: dict[str, dict[str, MemoryVector]],
        exc: Exception | None = None,
    ) -> None:
        """
        Roll back a partially completed transaction.

        Args:
            contexts: Dictionary mapping store names to transaction contexts
            snapshots: Dictionary mapping store names to normalized snapshots
            vector_snapshots: Dictionary mapping store names to vector snapshots
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
            if adapter is None:
                continue

            try:
                records = snap.get("records", {})
                vectors = vector_snapshots.get(name, {})

                current_items = self._get_all_items(adapter, store_name=name)
                current_ids = {item.id for item in current_items}
                for item_id in current_ids - set(records.keys()):
                    if hasattr(adapter, "delete"):
                        adapter.delete(item_id)
                        logger.debug(f"Deleted added item {item_id} from {name}")
                for item_id, record in records.items():
                    if hasattr(adapter, "store"):
                        adapter.store(record.item)
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

        # Clear any queued updates that shouldn't be applied and flush adapters
        with self._queue_lock:
            self._queue = []
        try:
            # Ensure adapters reflect the rolled back state
            self.memory_manager.flush_updates()
        except Exception:  # pragma: no cover - defensive
            logger.debug("Adapter flush after rollback failed", exc_info=True)
        # Any cached query results are now stale
        self.clear_cache()

    def _sync_one_way(
        self, source_adapter: MemoryAdapter, target_adapter: MemoryAdapter
    ) -> int:
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
        source_label = self._adapter_label(source_adapter, "source")
        for item in self._get_all_items(source_adapter, store_name=source_label):
            to_store: MemoryItem = item
            existing_record: MemoryRecord | None = None
            if hasattr(target_adapter, "retrieve"):
                existing_raw = target_adapter.retrieve(item.id)
                if existing_raw is not None:
                    existing_record = self._build_record(
                        existing_raw, source=source_label
                    )
            if existing_record is not None and self._detect_conflict(
                existing_record.item, item
            ):
                to_store = self._resolve_conflict(existing_record.item, item)
            elif existing_record is not None:
                to_store = existing_record.item
            if hasattr(target_adapter, "store"):
                target_adapter.store(to_store)
                count += 1
                self.stats.synchronized += 1
            if (
                existing_record is not None
                and to_store is existing_record.item
                and hasattr(source_adapter, "store")
            ):
                source_adapter.store(existing_record.item)

        # Synchronize vectors
        for vector in self._get_all_vectors(source_adapter):
            existing_vec = None
            if hasattr(target_adapter, "retrieve_vector"):
                existing_vec = target_adapter.retrieve_vector(vector.id)
            if existing_vec is None and hasattr(target_adapter, "store_vector"):
                target_adapter.store_vector(vector)
                count += 1
                self.stats.synchronized += 1

        return count

    def synchronize(
        self, source: str, target: str, bidirectional: bool = False
    ) -> dict[str, int]:
        """Synchronize items from ``source`` to ``target`` transactionally.

        If ``bidirectional`` is ``True``, the reverse synchronization is
        performed within the same transaction to ensure atomicity across both
        directions.
        """

        source_adapter = self.memory_manager.adapters.get(source)
        target_adapter = self.memory_manager.adapters.get(target)
        if source_adapter is None or target_adapter is None:
            logger.warning(
                "Sync skipped due to missing adapters: %s -> %s", source, target
            )
            return {f"{source}_to_{target}": 0}

        result: dict[str, int] = {}

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

    def synchronize_core(self) -> dict[str, int]:
        """Synchronize LMDB and FAISS stores into the Kuzu store.

        This helper coordinates synchronization across the primary persistent
        backends used by the memory system. If any of the stores are missing
        the operation is skipped for that pair. The method returns a mapping of
        performed synchronization directions to the number of items synced.

        Returns:
            Mapping of synchronization directions to counts.
        """

        results: dict[str, int] = {}
        adapters: AdapterRegistry = self.memory_manager.adapters

        # Ensure Kuzu is available as the central store
        if "kuzu" not in adapters:
            return results

        stores: list[str] = ["kuzu"]
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

    def update_item(self, store: str, item: MemoryItem | MemoryRecord) -> bool:
        """Update ``item`` in ``store`` and propagate to other adapters.

        Incoming payloads are normalized into :class:`MemoryRecord` entries so
        downstream adapters receive consistent metadata regardless of the
        originating store.
        """

        adapter = self.memory_manager.adapters.get(store)
        if adapter is None:
            return False

        record = self._build_record(item, source=store)
        primary_item = record.item

        if hasattr(adapter, "store"):
            adapter.store(primary_item)
        for name, other in self.memory_manager.adapters.items():
            if name == store or not hasattr(other, "store"):
                continue
            existing: MemoryRecordInput | None = None
            existing_record: MemoryRecord | None = None
            if hasattr(other, "retrieve"):
                existing = other.retrieve(primary_item.id)
            to_store = primary_item
            if existing is not None:
                existing_record = self._build_record(existing, source=name)
                if self._detect_conflict(existing_record.item, primary_item):
                    to_store = self._resolve_conflict(
                        existing_record.item, primary_item
                    )
                else:
                    to_store = existing_record.item
            other.store(to_store)
            if (
                existing is not None
                and existing_record is not None
                and to_store is existing_record.item
                and hasattr(adapter, "store")
            ):
                adapter.store(existing_record.item)
        self.stats.synchronized += 1
        try:
            self.memory_manager._notify_sync_hooks(primary_item)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)
        # Memory contents have changed; invalidate any cached queries so
        # subsequent cross-store lookups see the update immediately.
        self.clear_cache()
        return True

    def queue_update(
        self,
        store: str,
        item: MemoryItem | MemoryRecord,
        *,
        transaction_id: str | None = None,
    ) -> None:
        """Queue an update for asynchronous propagation.

        The update is coerced into a :class:`MemoryRecord` immediately so the
        queue retains DTO-normalized entries even if adapters emit raw domain
        models.
        """

        record = self._build_record(item, source=store)
        entry: QueuedUpdate = {
            "store": store,
            "record": record,
            "transaction_id": transaction_id,
        }
        with self._queue_lock:
            self._queue.append(entry)
        if self.async_mode:
            self.schedule_flush()
        try:
            self.memory_manager._notify_sync_hooks(record.item)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)
        # Queueing a new update means cached query results may be stale.
        self.clear_cache()

    def flush_queue(self) -> None:
        """Propagate all queued updates.

        Each queued entry already contains a :class:`MemoryRecord` so flushing
        reuses normalized DTOs and clears cached query results to avoid serving
        stale metadata.
        """
        while True:
            with self._queue_lock:
                if not self._queue:
                    break
                entry = self._queue.pop(0)
            self.update_item(entry["store"], entry["record"])
        with self._queue_lock:
            self._queue = []
        try:
            self.memory_manager._notify_sync_hooks(None)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)
        # After the queue is flushed the cache no longer reflects previous
        # state, so clear it to force fresh queries.
        self.clear_cache()

    async def flush_queue_async(self) -> None:
        """Asynchronously propagate queued updates with DTO normalization."""
        while True:
            with self._queue_lock:
                if not self._queue:
                    break
                entry = self._queue.pop(0)
            self.update_item(entry["store"], entry["record"])
            await asyncio.sleep(0)
        with self._queue_lock:
            self._queue = []
        try:
            self.memory_manager._notify_sync_hooks(None)
        except Exception as exc:
            logger.warning("Peer review failed: %s", exc)
        # Keep cache coherent with the underlying stores.
        self.clear_cache()

    def schedule_flush(self, delay: float = 0.1) -> None:
        async def _delayed() -> None:
            await asyncio.sleep(delay)
            await self.flush_queue_async()

        task: asyncio.Task[None] = asyncio.create_task(_delayed())
        self._async_tasks.append(task)

    async def wait_for_async(self) -> None:
        if self._async_tasks:
            await asyncio.gather(*self._async_tasks)
            self._async_tasks = []

    def cross_store_query(
        self, query: str, stores: list[str] | None = None
    ) -> GroupedMemoryResults:
        """Query multiple stores and cache normalized DTO results.

        Each adapter's response is coerced into :class:`MemoryRecord` entries
        and stored inside a :class:`GroupedMemoryResults` mapping.  The cache
        therefore contains fully-normalized DTO payloads whose metadata has
        already been merged.
        """

        key_stores = ",".join(sorted(stores)) if stores else "all"
        cache_key = f"{query}:{key_stores}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        target_stores = stores or list(self.memory_manager.adapters.keys())
        grouped: GroupedMemoryResults = {"by_store": {}, "query": query}
        combined: list[MemoryRecord] = []
        for name in target_stores:
            adapter = self.memory_manager.adapters.get(name)
            if adapter is None:
                continue
            label = self._adapter_label(adapter, name)
            if isinstance(adapter, VectorStoreProtocol):
                embedding = self.memory_manager._embed_text(
                    query, getattr(adapter, "dimension", 5)
                )
                raw_results = adapter.similarity_search(embedding, top_k=5)
            elif isinstance(adapter, SupportsSearch):
                raw_results = adapter.search({"content": query})
            else:
                raw_results = []
            records = self._normalize_records(raw_results, source=label)
            combined.extend(records)
            store_results: MemoryQueryResults = {
                "store": label,
                "records": records,
            }
            grouped["by_store"][label] = store_results

        if combined:
            grouped["combined"] = combined
        self.cache.put(cache_key, grouped)
        return grouped

    async def cross_store_query_async(
        self, query: str, stores: list[str] | None = None
    ) -> GroupedMemoryResults:
        """Asynchronously query multiple stores and cache normalized results."""

        key_stores = ",".join(sorted(stores)) if stores else "all"
        cache_key = f"{query}:{key_stores}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        target_stores = stores or list(self.memory_manager.adapters.keys())

        async def _query(name: str) -> tuple[str, str, Iterable[MemoryRecordInput]]:
            adapter = self.memory_manager.adapters.get(name)
            if adapter is None:
                return name, name, []
            label = self._adapter_label(adapter, name)
            if isinstance(adapter, VectorStoreProtocol):
                embedding = self.memory_manager._embed_text(
                    query, getattr(adapter, "dimension", 5)
                )
                result = await asyncio.to_thread(
                    adapter.similarity_search,
                    embedding,
                    top_k=5,
                )
                return name, label, result
            if isinstance(adapter, SupportsSearch):
                result = await asyncio.to_thread(adapter.search, {"content": query})
                if isinstance(result, Sequence) and not isinstance(
                    result, (str, bytes)
                ):
                    return name, label, list(result)
                if isinstance(result, Mapping):
                    records = result.get("records") or result.get("combined") or []
                    return name, label, cast(Iterable[MemoryRecordInput], records)
                return name, label, []
            return name, label, []

        pairs = await asyncio.gather(*(_query(name) for name in target_stores))
        grouped: GroupedMemoryResults = {"by_store": {}, "query": query}
        combined: list[MemoryRecord] = []
        for _, label, raw_items in pairs:
            records = self._normalize_records(raw_items, source=label)
            combined.extend(records)
            grouped["by_store"][label] = {"store": label, "records": records}
        if combined:
            grouped["combined"] = combined
        self.cache.put(cache_key, grouped)
        return grouped

    def clear_cache(self) -> None:
        """Clear cached query results."""

        self.cache.clear()

    def get_cache_size(self) -> int:
        """Return number of cached queries."""

        return self.cache.size()

    # ------------------------------------------------------------------
    def get_sync_stats(self) -> dict[str, int]:
        """Return statistics about synchronization operations."""

        return self.stats.as_dict()

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
        snapshots: dict[str, AdapterSnapshot] = {}
        vector_snapshots: dict[str, dict[str, MemoryVector]] = {}
        contexts: dict[str, TransactionContextManager] = {}
        txns: dict[str, object] = {}

        # Begin transaction for each store
        for name in stores:
            adapter = self.memory_manager.adapters.get(name)
            if adapter is None:
                continue
            ctx = self._get_transaction_context(adapter, tx_id)
            if ctx is not None:
                txns[name] = ctx.__enter__()
                contexts[name] = ctx
                continue

            items = self._get_all_items(adapter, store_name=name)
            vectors = self._get_all_vectors(adapter)
            normalized = self._normalize_records(items, source=name)
            snapshots[name] = {
                "store": name,
                "records": {record.id: record for record in normalized},
            }
            if vectors:
                vector_snapshots[name] = {vec.id: deepcopy(vec) for vec in vectors}

        # Store transaction state
        self._active_transactions[tx_id] = TransactionState(
            stores=stores,
            snapshots=snapshots,
            vector_snapshots=vector_snapshots,
            contexts=contexts,
            txns=txns,
            started_at=datetime.now(),
        )

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
        contexts = transaction.contexts

        # Commit transaction for each store
        for ctx in contexts.values():
            ctx.__exit__(None, None, None)

        # Flush any queued updates to ensure persistence across stores
        try:
            self.flush_queue()
            if self.async_mode:
                asyncio.run(self.wait_for_async())
            # Flush underlying adapters so cross-store updates are durable
            self.memory_manager.flush_updates()
        except Exception as e:
            logger.error(
                f"Error flushing updates for transaction {transaction_id}: {e}"
            )

        # Remove transaction state
        del self._active_transactions[transaction_id]
        # Any cached query results are now stale
        self.clear_cache()

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

        self._rollback_partial_transaction(
            transaction.contexts,
            transaction.snapshots,
            transaction.vector_snapshots,
            ValueError("Transaction rolled back"),
        )

        # Remove transaction state
        del self._active_transactions[transaction_id]

    # ------------------------------------------------------------------
    def is_transaction_active(self, transaction_id: str) -> bool:
        """Return ``True`` if ``transaction_id`` is currently active."""

        return transaction_id in self._active_transactions
