"""Memory Integration Manager leveraging typed DTO abstractions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Mapping, Optional, cast

from devsynth.application.memory.dto import (
    MemoryMetadata,
    MemoryRecord,
    build_memory_record,
)
from devsynth.exceptions import MemoryError, MemoryItemNotFoundError, MemoryStoreError

from ...domain.interfaces.memory import MemorySearchResponse, MemoryStore, VectorStore
from ...domain.models.memory import MemoryItem, MemoryType, MemoryVector
from ...logging_setup import DevSynthLogger

if TYPE_CHECKING:  # pragma: no cover - typing imports only
    from devsynth.application.memory.dto import GroupedMemoryResults, MemoryQueryResults

logger = DevSynthLogger(__name__)


def _records_from_response(
    response: MemorySearchResponse, store_name: str
) -> list[MemoryRecord]:
    """Normalize search responses into :class:`MemoryRecord` instances."""

    if isinstance(response, list):
        return [build_memory_record(item, source=store_name) for item in response]

    if isinstance(response, dict):
        if "by_store" in response:
            grouped_records: list[MemoryRecord] = []
            by_store = cast("GroupedMemoryResults", response)["by_store"]
            for nested_store, payload in by_store.items():
                grouped_records.extend(_records_from_response(payload, nested_store))
            combined = cast("GroupedMemoryResults", response).get("combined")
            if combined:
                grouped_records.extend(
                    build_memory_record(record, source=store_name)
                    for record in combined
                )
            return grouped_records

        if "records" in response:
            query_results = cast("MemoryQueryResults", response)
            result_store = query_results.get("store", store_name)
            return [
                build_memory_record(record, source=result_store)
                for record in query_results.get("records", [])
            ]

    return []


def _clone_item(record: MemoryRecord) -> MemoryItem:
    """Create a mutable :class:`MemoryItem` copy from a memory record."""

    metadata: MemoryMetadata = cast(MemoryMetadata, dict(record.metadata or {}))
    return MemoryItem(
        id=record.item.id,
        content=record.item.content,
        memory_type=record.item.memory_type,
        metadata=metadata,
        created_at=record.item.created_at,
    )


class MemoryIntegrationManager:
    """
    Memory Integration Manager facilitates integration between different memory stores.

    This class provides methods for transferring and synchronizing data between
    different memory stores, enabling a unified memory system with different
    storage backends.
    """

    def __init__(self):
        """Initialize the Memory Integration Manager."""
        self.memory_stores: dict[str, MemoryStore] = {}
        self.vector_stores: dict[str, VectorStore[MemoryVector]] = {}
        logger.info("Memory Integration Manager initialized")

    def register_memory_store(self, name: str, store: MemoryStore) -> None:
        """
        Register a memory store with the integration manager.

        Args:
            name: A unique name for the memory store
            store: The memory store to register
        """
        self.memory_stores[name] = store
        logger.info(f"Registered memory store '{name}'")

    def register_vector_store(
        self, name: str, store: VectorStore[MemoryVector]
    ) -> None:
        """
        Register a vector store with the integration manager.

        Args:
            name: A unique name for the vector store
            store: The vector store to register
        """
        self.vector_stores[name] = store
        logger.info(f"Registered vector store '{name}'")

    def transfer_item(self, item_id: str, source_store: str, target_store: str) -> str:
        """
        Transfer a memory item from one store to another.

        Args:
            item_id: The ID of the memory item to transfer
            source_store: The name of the source memory store
            target_store: The name of the target memory store

        Returns:
            The ID of the transferred memory item in the target store

        Raises:
            MemoryStoreError: If the source or target store is not registered,
                             or if the item cannot be retrieved or stored
        """
        try:
            # Check if stores are registered
            if source_store not in self.memory_stores:
                raise MemoryStoreError(f"Source store '{source_store}' not registered")
            if target_store not in self.memory_stores:
                raise MemoryStoreError(f"Target store '{target_store}' not registered")

            # Retrieve the item from the source store
            item_payload = self.memory_stores[source_store].retrieve(item_id)
            if item_payload is None:
                raise MemoryItemNotFoundError(
                    f"Item with ID {item_id} not found in source store '{source_store}'"
                )

            record = build_memory_record(item_payload, source=source_store)
            item = _clone_item(record)

            # Add transfer metadata
            item.metadata["transferred_from"] = source_store
            item.metadata["transferred_at"] = datetime.now().isoformat()

            # Store the item in the target store
            new_id = self.memory_stores[target_store].store(item)

            logger.info(
                f"Transferred memory item with ID {item_id} from '{source_store}' to '{target_store}' with new ID {new_id}"
            )
            return new_id
        except Exception as e:
            logger.error(f"Failed to transfer memory item: {e}")
            raise MemoryStoreError(f"Failed to transfer memory item: {e}")

    def synchronize_stores(
        self, store1: str, store2: str, bidirectional: bool = True
    ) -> dict[str, int]:
        """
        Synchronize memory items between two stores.

        Args:
            store1: The name of the first memory store
            store2: The name of the second memory store
            bidirectional: Whether to synchronize in both directions

        Returns:
            A dictionary with the number of items transferred in each direction

        Raises:
            MemoryStoreError: If either store is not registered
        """
        try:
            # Check if stores are registered
            if store1 not in self.memory_stores:
                raise MemoryStoreError(f"Store '{store1}' not registered")
            if store2 not in self.memory_stores:
                raise MemoryStoreError(f"Store '{store2}' not registered")

            # Get all items from store1
            store1_items = self.memory_stores[store1].search({})
            store1_records = _records_from_response(store1_items, store1)

            # Transfer items from store1 to store2
            transferred_to_store2 = 0
            for record in store1_records:
                item = _clone_item(record)
                item.metadata["synchronized_from"] = store1
                item.metadata["synchronized_at"] = datetime.now().isoformat()

                # Store the item in store2
                self.memory_stores[store2].store(item)
                transferred_to_store2 += 1

            result = {f"{store1}_to_{store2}": transferred_to_store2}

            # If bidirectional, also transfer from store2 to store1
            if bidirectional:
                # Get all items from store2
                store2_items = self.memory_stores[store2].search({})
                store2_records = _records_from_response(store2_items, store2)

                # Transfer items from store2 to store1
                transferred_to_store1 = 0
                for record in store2_records:
                    # Skip items that were just transferred from store1
                    source_store = record.item.metadata.get("synchronized_from")
                    if source_store == store1:
                        continue

                    # Add synchronization metadata
                    item = _clone_item(record)
                    item.metadata["synchronized_from"] = store2
                    item.metadata["synchronized_at"] = datetime.now().isoformat()

                    # Store the item in store1
                    self.memory_stores[store1].store(item)
                    transferred_to_store1 += 1

                result[f"{store2}_to_{store1}"] = transferred_to_store1

            logger.info(
                f"Synchronized memory stores '{store1}' and '{store2}': {result}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to synchronize memory stores: {e}")
            raise MemoryStoreError(f"Failed to synchronize memory stores: {e}")

    def query_across_stores(
        self,
        query: Mapping[str, object] | MemoryMetadata,
        stores: list[str] | None = None,
    ) -> dict[str, MemorySearchResponse]:
        """
        Query for memory items across multiple stores.

        Args:
            query: The query dictionary or metadata filter
            stores: A list of store names to query, or None to query all registered stores

        Returns:
            A dictionary mapping store names to typed memory search responses

        Raises:
            MemoryStoreError: If any of the specified stores is not registered
        """
        try:
            # If no stores specified, use all registered stores
            if not stores:
                stores = list(self.memory_stores.keys())

            # Check if all specified stores are registered
            for store in stores:
                if store not in self.memory_stores:
                    raise MemoryStoreError(f"Store '{store}' not registered")

            # Query each store
            results: dict[str, MemorySearchResponse] = {}
            for store in stores:
                store_results = self.memory_stores[store].search(query)
                results[store] = store_results

            logger.info(f"Queried {len(stores)} memory stores with query: {query}")
            return results
        except Exception as e:
            logger.error(f"Failed to query across memory stores: {e}")
            raise MemoryStoreError(f"Failed to query across memory stores: {e}")

    def apply_volatility_across_stores(
        self, decay_rate: float = 0.1, threshold: float = 0.5
    ) -> dict[str, list[str]]:
        """
        Apply memory volatility controls across all registered stores that support it.

        Args:
            decay_rate: The rate at which confidence decays (0.0 to 1.0)
            threshold: The confidence threshold below which items are considered volatile

        Returns:
            A dictionary mapping store names to lists of volatile item IDs
        """
        try:
            results = {}

            for name, store in self.memory_stores.items():
                # Check if the store supports memory volatility
                if hasattr(store, "add_memory_volatility") and hasattr(
                    store, "apply_memory_decay"
                ):
                    # Add memory volatility controls
                    store.add_memory_volatility(decay_rate, threshold)

                    # Apply memory decay
                    volatile_items = store.apply_memory_decay()
                    results[name] = volatile_items

                    logger.info(
                        f"Applied memory volatility to store '{name}', {len(volatile_items)} volatile items"
                    )
                else:
                    logger.warning(f"Store '{name}' does not support memory volatility")

            return results
        except Exception as e:
            logger.error(f"Failed to apply memory volatility across stores: {e}")
            raise MemoryStoreError(
                f"Failed to apply memory volatility across stores: {e}"
            )
