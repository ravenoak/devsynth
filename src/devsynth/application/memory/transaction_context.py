"""Transaction context for cross-store memory operations.

The transaction workflow captures adapter state using
``MemoryRecord``-backed DTOs so metadata remains normalized when snapshots are
created, committed, or restored.  This ensures recovery logs provide enough
detail to audit synchronization decisions and to repopulate caches after
rollbacks.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from types import TracebackType
from typing import Literal, Protocol, TypedDict, runtime_checkable

from ...domain.models.memory import MemoryItem
from ...exceptions import MemoryTransactionError
from ...logging_setup import DevSynthLogger
from .adapter_types import MemoryAdapter
from .dto import MemoryRecord, MemoryRecordInput, build_memory_record

logger = DevSynthLogger(__name__)


@runtime_checkable
class SupportsTransactionalStore(Protocol):
    """Protocol for adapters that expose transaction primitives."""

    def begin_transaction(
        self, transaction_id: str
    ) -> None:  # pragma: no cover - protocol
        ...

    def commit_transaction(
        self, transaction_id: str
    ) -> None:  # pragma: no cover - protocol
        ...

    def rollback_transaction(
        self, transaction_id: str
    ) -> None:  # pragma: no cover - protocol
        ...


@runtime_checkable
class SupportsFlushUpdates(Protocol):
    def flush_updates(self) -> None:  # pragma: no cover - protocol
        ...


@runtime_checkable
class SupportsFlushPendingWrites(Protocol):
    def flush_pending_writes(self) -> None:  # pragma: no cover - protocol
        ...


@runtime_checkable
class SupportsFlushQueue(Protocol):
    def flush_queue(self) -> None:  # pragma: no cover - protocol
        ...


@runtime_checkable
class SupportsGenericFlush(Protocol):
    def flush(self) -> None:  # pragma: no cover - protocol
        ...


class AdapterSnapshot(TypedDict):
    store: str
    records: dict[str, MemoryRecord]


OperationPhase = Literal["snapshot", "commit", "rollback"]


class OperationLogEntry(TypedDict):
    store: str
    phase: OperationPhase
    records: list[MemoryRecord]


class TransactionContext:
    """
    Transaction context for memory operations across multiple adapters.

    This class implements a two-phase commit protocol for cross-store transactions.
    It handles adapters with and without native transaction support and records
    each phase using :class:`MemoryRecord` entries so recovery tooling can
    inspect the normalized operation log.
    """

    def __init__(self, adapters: Sequence[MemoryAdapter]):
        """
        Initialize the transaction context.

        Args:
            adapters: List of memory adapters to include in the transaction
        """
        self.adapters: list[MemoryAdapter] = list(adapters)
        self.transaction_id = str(uuid.uuid4())
        self.snapshots: dict[int, AdapterSnapshot] = {}
        self.operations: list[OperationLogEntry] = []
        self.prepared_adapters: list[MemoryAdapter] = []

    def __enter__(self) -> TransactionContext:
        """
        Begin the transaction on all adapters.

        For adapters with native transaction support, call begin_transaction.
        For adapters without native transaction support, take a snapshot of the current state.

        Returns:
            self: The transaction context

        Raises:
            MemoryTransactionError: If the transaction cannot be started
        """
        logger.debug(
            f"Starting transaction {self.transaction_id} for {len(self.adapters)} adapters"
        )

        try:
            for adapter in self.adapters:
                label = self._adapter_label(adapter)
                if isinstance(adapter, SupportsTransactionalStore):
                    begin = getattr(adapter, "begin_transaction", None)
                    try:
                        if callable(begin):
                            begin(self.transaction_id)
                    except TypeError:
                        if callable(begin):
                            begin()
                    self._record_operation(label, "snapshot", [])
                    continue

                snapshot = self._snapshot_adapter_state(adapter, label)
                self.snapshots[id(adapter)] = {"store": label, "records": snapshot}
                self._record_operation(label, "snapshot", snapshot.values())

                logger.debug(
                    "Created snapshot for %s with %d items",
                    label,
                    len(snapshot),
                )
        except Exception as e:
            # If begin_transaction fails, rollback any adapters that were already started
            self._rollback()
            raise MemoryTransactionError(f"Failed to start transaction: {e}")

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """
        End the transaction on all adapters.

        If no exception occurred, commit the transaction.
        If an exception occurred, rollback the transaction.

        Args:
            exc_type: Exception type, if an exception occurred
            exc_val: Exception value, if an exception occurred
            exc_tb: Exception traceback, if an exception occurred

        Returns:
            bool: True if the exception was handled, False otherwise
        """
        if exc_type is None:
            # No exception occurred, commit the transaction
            try:
                self._commit()
                return True
            except Exception as e:
                logger.error(f"Failed to commit transaction {self.transaction_id}: {e}")
                self._rollback()
                raise MemoryTransactionError(f"Failed to commit transaction: {e}")
        else:
            # Exception occurred, rollback the transaction
            logger.error(f"Transaction {self.transaction_id} failed: {exc_val}")
            self._rollback()
            return False

    def _commit(self) -> None:
        """
        Commit the transaction using a two-phase commit protocol.

        Phase 1: Prepare all adapters for commit
        Phase 2: Commit all adapters

        If any adapter fails to prepare, rollback all adapters.

        Raises:
            MemoryTransactionError: If the transaction cannot be committed
        """
        logger.debug(f"Committing transaction {self.transaction_id}")

        # Phase 1: Flush and prepare
        try:
            for adapter in self.adapters:
                self._flush_adapter(adapter)
                prepare = getattr(adapter, "prepare_commit", None)
                if callable(prepare):
                    try:
                        prepare(self.transaction_id)
                    except TypeError:
                        prepare()
                    self.prepared_adapters.append(adapter)
        except Exception as e:
            # If prepare fails, rollback all adapters
            logger.error(f"Failed to prepare transaction {self.transaction_id}: {e}")
            self._rollback()
            raise MemoryTransactionError(f"Failed to prepare transaction: {e}")

        # Phase 2: Flush and commit
        commit_errors: list[str] = []
        committed_snapshots: list[tuple[str, list[MemoryRecord]]] = []
        for adapter in self.adapters:
            label = self._adapter_label(adapter)
            try:
                self._flush_adapter(adapter)
                commit = getattr(adapter, "commit_transaction", None)
                if callable(commit):
                    try:
                        commit(self.transaction_id)
                    except TypeError:
                        commit()
                snapshot_records = list(
                    self._snapshot_adapter_state(adapter, label).values()
                )
                committed_snapshots.append((label, snapshot_records))
            except Exception as e:
                error_msg = (
                    f"Failed to commit transaction {self.transaction_id} on "
                    f"{adapter.__class__.__name__}: {e}"
                )
                logger.error(error_msg)
                commit_errors.append(error_msg)

        for label, records in committed_snapshots:
            self._record_operation(label, "commit", records)

        if commit_errors:
            # If any commit fails, log the errors but don't rollback
            # (we're in an inconsistent state, but rolling back might make it worse)
            logger.error(
                f"Transaction {self.transaction_id} partially committed with errors: {commit_errors}"
            )
            raise MemoryTransactionError(
                f"Transaction partially committed with errors: {commit_errors}"
            )

        logger.debug(f"Transaction {self.transaction_id} committed successfully")

    def _flush_adapter(self, adapter: MemoryAdapter) -> None:
        """Flush pending writes for an adapter if supported."""

        label = self._adapter_label(adapter)
        if isinstance(adapter, SupportsFlushUpdates):
            logger.debug("Flushing pending writes for %s using flush_updates", label)
            adapter.flush_updates()
            return
        if isinstance(adapter, SupportsFlushPendingWrites):
            logger.debug(
                "Flushing pending writes for %s using flush_pending_writes", label
            )
            adapter.flush_pending_writes()
            return
        if isinstance(adapter, SupportsFlushQueue):
            logger.debug("Flushing pending writes for %s using flush_queue", label)
            adapter.flush_queue()
            return
        if isinstance(adapter, SupportsGenericFlush):
            logger.debug("Flushing pending writes for %s using flush", label)
            adapter.flush()
            return

        # Fallback to duck typing for adapters not covered by the protocols.
        for method_name in (
            "flush_updates",
            "flush_pending_writes",
            "flush_queue",
            "flush",
        ):
            method = getattr(adapter, method_name, None)
            if callable(method):
                logger.debug(
                    "Flushing pending writes for %s using %s", label, method_name
                )
                method()
                break

    def _rollback(self) -> None:
        """
        Rollback the transaction on all adapters.

        For adapters with native transaction support, call rollback_transaction.
        For adapters without native transaction support, restore from snapshot.
        """
        logger.debug(f"Rolling back transaction {self.transaction_id}")

        rollback_errors = []

        # Rollback adapters with native transaction support
        for adapter in self.adapters:
            label = self._adapter_label(adapter)
            try:
                rollback = getattr(adapter, "rollback_transaction", None)
                if callable(rollback):
                    try:
                        rollback(self.transaction_id)
                    except TypeError:
                        rollback()
                    restored = self._snapshot_adapter_state(adapter, label)
                    self._record_operation(label, "rollback", restored.values())
            except Exception as e:
                error_msg = f"Failed to rollback transaction {self.transaction_id} on {adapter.__class__.__name__}: {e}"
                logger.error(error_msg)
                rollback_errors.append(error_msg)

        # Restore snapshots for adapters without native transaction support
        for adapter in self.adapters:
            if hasattr(adapter, "rollback_transaction"):
                continue
            adapter_id = id(adapter)
            snapshot = self.snapshots.get(adapter_id)
            if not snapshot:
                continue
            label = snapshot["store"]
            try:
                # Delete all items and restore from snapshot using normalized DTOs.
                if hasattr(adapter, "delete"):
                    current_state = self._snapshot_adapter_state(adapter, label)
                    for record in current_state.values():
                        adapter.delete(record.id)

                if hasattr(adapter, "store"):
                    for record in snapshot["records"].values():
                        adapter.store(record.item)
                self._record_operation(label, "rollback", snapshot["records"].values())
            except Exception as e:
                error_msg = (
                    f"Failed to restore snapshot for {adapter.__class__.__name__}: {e}"
                )
                logger.error(error_msg)
                rollback_errors.append(error_msg)

        if rollback_errors:
            logger.error(
                f"Transaction {self.transaction_id} rollback completed with errors: {rollback_errors}"
            )
        else:
            logger.debug(f"Transaction {self.transaction_id} rolled back successfully")

    def _adapter_label(self, adapter: MemoryAdapter) -> str:
        """Return a human readable name for ``adapter``."""

        label = getattr(adapter, "name", None)
        if isinstance(label, str) and label:
            return label
        return adapter.__class__.__name__

    def _ensure_record(self, payload: MemoryRecordInput, store: str) -> MemoryRecord:
        """Normalize ``payload`` into a :class:`MemoryRecord`."""

        record = build_memory_record(payload, source=store)
        if not record.item.id:
            record.item.id = str(uuid.uuid4())
        return record

    def _snapshot_adapter_state(
        self, adapter: MemoryAdapter, store: str
    ) -> dict[str, MemoryRecord]:
        """Capture the adapter state as ``MemoryRecord`` entries."""

        snapshot: dict[str, MemoryRecord] = {}
        get_all = getattr(adapter, "get_all", None)
        get_all_items = getattr(adapter, "get_all_items", None)
        items: Iterable[MemoryRecordInput] | None = None
        if callable(get_all):
            items = get_all()
        elif callable(get_all_items):
            items = get_all_items()

        if items is None:
            logger.warning(
                "Adapter %s does not expose a snapshot API; snapshot will be empty",
                store,
            )
            return snapshot

        for payload in items:
            record = self._ensure_record(payload, store)
            snapshot[record.id] = record
        return snapshot

    def _record_operation(
        self, store: str, phase: OperationPhase, records: Iterable[MemoryRecord]
    ) -> None:
        """Append a normalized entry to the operation log."""

        normalized = [self._ensure_record(record, store) for record in records]
        entry: OperationLogEntry = {
            "store": store,
            "phase": phase,
            "records": normalized,
        }
        self.operations.append(entry)
