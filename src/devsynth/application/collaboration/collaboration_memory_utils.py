"""
Utility functions for integrating collaboration entities with the memory system.

This module provides serialization/deserialization methods for collaboration entities
to convert between domain objects and memory items.
"""

import json
import random
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    cast,
)
from collections.abc import Awaitable, Coroutine, Iterable, Mapping

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger

from .agent_collaboration import AgentMessage, CollaborationTask
from .dto import ensure_memory_sync_port, serialize_memory_sync_port
from .structures import MemoryQueueEntry, ReviewCycleSpec

PeerReview: type[Any] | None
try:  # pragma: no cover - optional dependency
    from .peer_review import PeerReview as _PeerReview
except Exception:  # pragma: no cover - optional dependency
    _PeerReview = None
PeerReview = cast(Optional[type[Any]], _PeerReview)

logger = DevSynthLogger(__name__)


async def _await_result(awaitable: Awaitable[Any]) -> Any:
    """Await an arbitrary awaitable object."""

    return await awaitable


def _resolve_entity_id(entity: Any) -> str:
    """Return a stable string identifier for an entity."""

    identifier = getattr(entity, "id", None) or getattr(entity, "review_id", None)
    if identifier is None:
        return str(id(entity))
    return str(identifier)


def flush_memory_queue(memory_manager: Any) -> list[MemoryQueueEntry]:
    """Flush queued memory updates and return flushed items deterministically.

    The sync manager maintains an internal queue protected by ``_queue_lock``.
    This helper snapshots the queue under that lock, performs a flush, waits for
    any asynchronous synchronization to finish, and *does not* clear the queue
    again afterwards. Clearing is handled by the sync manager itself during the
    flush to avoid races with new updates being queued concurrently.

    Args:
        memory_manager: The memory manager instance coordinating updates.

    Returns:
        List of ``(store, MemoryItem)`` tuples that were flushed.
    """

    if not memory_manager or not hasattr(memory_manager, "sync_manager"):
        return []

    sync_manager = memory_manager.sync_manager
    lock = getattr(sync_manager, "_queue_lock", None)
    if lock:
        with lock:
            queue_snapshot: list[tuple[str, MemoryItem]] = list(
                getattr(sync_manager, "_queue", [])
            )
    else:
        queue_snapshot = list(getattr(sync_manager, "_queue", []))

    normalized_queue: list[MemoryQueueEntry] = []
    for store, item in queue_snapshot:
        if item.metadata and "sync_port" in item.metadata:
            try:
                item.metadata["sync_port"] = ensure_memory_sync_port(
                    item.metadata["sync_port"]
                )
            except Exception:  # pragma: no cover - defensive
                logger.debug("Failed to normalize sync_port metadata", exc_info=True)
        normalized_queue.append(MemoryQueueEntry(store=store, item=item))

    notified = False
    try:
        if hasattr(memory_manager, "flush_updates"):
            memory_manager.flush_updates()
            notified = True
        else:
            flush = getattr(sync_manager, "flush_queue", None)
            if callable(flush):
                flush()
                notified = True

        wait = getattr(memory_manager, "wait_for_sync", None)
        if not callable(wait):
            wait = getattr(sync_manager, "wait_for_async", None)
        if callable(wait):
            import asyncio
            import inspect

            result = wait()
            if inspect.isawaitable(result):  # pragma: no cover - depends on event loop
                if inspect.iscoroutine(result):
                    asyncio.run(cast(Coroutine[Any, Any, Any], result))
                else:
                    awaitable_result: Awaitable[Any] = result
                    asyncio.run(_await_result(awaitable_result))
    except Exception:  # pragma: no cover - defensive
        logger.debug("Flush failed", exc_info=True)
    finally:
        if not notified:
            notify = getattr(memory_manager, "_notify_sync_hooks", None)
            if callable(notify):
                try:
                    notify(None)
                except Exception:  # pragma: no cover - defensive
                    logger.debug("Sync hook notification failed", exc_info=True)

    return normalized_queue


def restore_memory_queue(
    memory_manager: Any,
    queued_items: Iterable[MemoryQueueEntry | tuple[str, MemoryItem]],
) -> None:
    """Requeue memory updates previously returned by :func:`flush_memory_queue`.

    Args:
        memory_manager: The memory manager handling updates.
        queued_items: Items to requeue in their original order.
    """

    if not memory_manager:
        return
    has_items = False
    for entry in queued_items:
        has_items = True
        if isinstance(entry, MemoryQueueEntry):
            store, item = entry.store, entry.item
        else:
            store, item = entry
        try:
            if item.metadata and "sync_port" in item.metadata:
                try:
                    item.metadata["sync_port"] = serialize_memory_sync_port(
                        ensure_memory_sync_port(item.metadata["sync_port"])
                    )
                except Exception:
                    logger.debug(
                        "Failed to serialize sync_port metadata", exc_info=True
                    )
            memory_manager.queue_update(store, item)
        except Exception:  # pragma: no cover - best effort
            logger.debug("Requeue failed", exc_info=True)
    if not has_items:
        return


def to_memory_item(entity: Any, memory_type: MemoryType) -> MemoryItem:
    """
    Convert a collaboration entity to a memory item.

    Args:
        entity: The collaboration entity to convert
        memory_type: The type of memory to store the entity as

    Returns:
        A MemoryItem representing the entity
    """
    if not entity:
        raise ValueError("Cannot convert None to MemoryItem")

    # Get entity ID
    entity_identifier = getattr(entity, "id", None) or getattr(
        entity, "review_id", None
    )
    if entity_identifier is None:
        raise ValueError(f"Entity {entity} does not have an id attribute")
    entity_id = str(entity_identifier)

    if hasattr(entity, "to_dict"):
        content = entity.to_dict()
    else:
        raise ValueError(f"Entity {entity} cannot be converted to a dictionary")

    use_custom_metadata = False
    metadata: dict[str, Any] = {}

    if hasattr(entity, "memory_metadata"):
        try:
            memory_metadata = getattr(entity, "memory_metadata")
            if callable(memory_metadata):
                metadata_candidate = memory_metadata()
                if isinstance(metadata_candidate, Mapping):
                    metadata = dict(metadata_candidate)
                elif isinstance(metadata_candidate, dict):
                    metadata = dict(metadata_candidate)
                elif metadata_candidate is not None:
                    metadata = dict(cast(Mapping[str, Any], metadata_candidate))
                use_custom_metadata = True
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug(
                "Failed to obtain custom memory metadata",
                extra={"entity": repr(entity), "error": str(exc)},
            )
            metadata = {}

    if not metadata:
        metadata = {
            "entity_type": entity.__class__.__name__,
            "created_at": datetime.now().isoformat(),
        }
    else:
        metadata.setdefault("entity_type", entity.__class__.__name__)

    if not use_custom_metadata:
        if isinstance(entity, CollaborationTask):
            metadata["task_type"] = entity.task_type
            metadata["status"] = (
                entity.status.name
                if hasattr(entity.status, "name")
                else str(entity.status)
            )
            if entity.parent_task_id:
                metadata["parent_task_id"] = entity.parent_task_id
            if entity.sync_port is not None:
                metadata["sync_port"] = serialize_memory_sync_port(entity.sync_port)
        elif isinstance(entity, AgentMessage):
            metadata["message_type"] = (
                entity.message_type.name
                if hasattr(entity.message_type, "name")
                else str(entity.message_type)
            )
            metadata["sender_id"] = entity.sender_id
            metadata["recipient_id"] = entity.recipient_id
            if entity.related_task_id:
                metadata["related_task_id"] = entity.related_task_id
        elif PeerReview is not None and isinstance(entity, PeerReview):
            metadata["status"] = entity.status
            metadata["author_id"] = getattr(entity.author, "id", str(entity.author))
            metadata["quality_score"] = entity.quality_score

    return MemoryItem(
        id=entity_id, content=content, memory_type=memory_type, metadata=metadata
    )


def from_memory_item(item: MemoryItem) -> Any:
    """
    Convert a memory item back to a collaboration entity.

    Args:
        item: The memory item to convert

    Returns:
        The collaboration entity
    """
    if not item:
        raise ValueError("Cannot convert None to entity")

    entity_type = item.metadata.get("entity_type")

    if entity_type == "CollaborationTask":
        return _memory_item_to_task(item)
    elif entity_type == "AgentMessage":
        return _memory_item_to_message(item)
    elif entity_type == "PeerReview":
        return _memory_item_to_review(item)
    else:
        logger.warning(f"Unknown entity type: {entity_type}")
        return item.content


def _memory_item_to_task(item: MemoryItem) -> CollaborationTask:
    """Convert a memory item to a CollaborationTask."""
    if not isinstance(item.content, dict):
        raise TypeError("Memory item content must be a mapping for CollaborationTask")

    content = dict(item.content)
    content.setdefault("id", item.id)

    metadata_sync = item.metadata.get("sync_port") if item.metadata else None
    if metadata_sync and "sync_port" not in content:
        content["sync_port"] = metadata_sync

    try:
        task = CollaborationTask.from_dict(content)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Failed to deserialize CollaborationTask: %s", exc)
        raise

    task.subtasks = []
    task.messages = []
    return task


def _memory_item_to_message(item: MemoryItem) -> AgentMessage:
    """Convert a memory item to an AgentMessage."""
    if not isinstance(item.content, dict):
        raise TypeError("Memory item content must be a mapping for AgentMessage")

    content = dict(item.content)
    content.setdefault("id", item.id)
    if item.metadata:
        content.setdefault("sender_id", item.metadata.get("sender_id"))
        content.setdefault("recipient_id", item.metadata.get("recipient_id"))
        content.setdefault("related_task_id", item.metadata.get("related_task_id"))

    return AgentMessage.from_dict(content)


def _memory_item_to_review(item: MemoryItem) -> Any:
    """
    Convert a memory item to a PeerReview with improved handling of complex attributes.

    This function creates a more complete PeerReview object by properly handling
    complex attributes like author, reviewers, and memory_manager.

    Args:
        item: The memory item to convert

    Returns:
        A reconstructed PeerReview object
    """
    # Import here to avoid circular imports
    from devsynth.application.memory.memory_manager import MemoryManager

    if PeerReview is None:
        return item.content

    content = item.content

    # Handle author - could be an agent object or a string
    author = content.get("author", "")
    # If author is a dict with an 'id' or 'name', it might be an agent reference
    if isinstance(author, dict) and ("id" in author or "name" in author):
        # In a real implementation, we might want to load the actual agent object
        # For now, we'll preserve the structure
        author_id = author.get("id", author.get("name", ""))
        if author_id:
            # This is a placeholder for agent reconstruction
            # In a production system, you might want to load the agent from a registry
            author = author

    # Handle reviewers - could be a list of agent objects or strings
    reviewers = content.get("reviewers", [])
    processed_reviewers: list[Any] = []
    for reviewer in reviewers:
        if isinstance(reviewer, dict) and ("id" in reviewer or "name" in reviewer):
            # Similar to author handling
            reviewer_id = reviewer.get("id", reviewer.get("name", ""))
            if reviewer_id:
                # Placeholder for reviewer reconstruction
                processed_reviewers.append(reviewer)
        else:
            processed_reviewers.append(reviewer)

    # Create the PeerReview object with basic attributes
    acceptance_data = content.get("acceptance_criteria")
    if acceptance_data is not None and not isinstance(acceptance_data, (list, tuple)):
        acceptance_data = [acceptance_data]

    quality_metrics = content.get("quality_metrics")
    if quality_metrics is not None and not isinstance(quality_metrics, Mapping):
        quality_metrics = None

    review_spec = ReviewCycleSpec(
        work_product=content.get("work_product", {}),
        author=author,
        reviewers=tuple(processed_reviewers),
        acceptance_criteria=acceptance_data,
        quality_metrics=quality_metrics,
        team=content.get("team"),
    )

    review = PeerReview(cycle=review_spec)

    # Set the review_id
    review.review_id = item.id

    # Set additional attributes
    review.status = content.get("status", "pending")
    review.quality_score = content.get("quality_score", 0.0)

    # Handle reviews dictionary - keys might be agent objects
    reviews_dict = content.get("reviews", {})
    processed_reviews: dict[Any, Any] = {}
    for reviewer_key, review_data in reviews_dict.items():
        # If the key is a string representation of an object, try to convert it
        if (
            isinstance(reviewer_key, str)
            and reviewer_key.startswith("<")
            and reviewer_key.endswith(">")
        ):
            # This is a placeholder for proper reviewer key reconstruction
            # In a real implementation, you might want to match this with actual reviewer objects
            for reviewer in processed_reviewers:
                if str(reviewer) == reviewer_key:
                    processed_reviews[reviewer] = review_data
                    break
            else:
                # If no match found, use the original key
                processed_reviews[reviewer_key] = review_data
        else:
            processed_reviews[reviewer_key] = review_data
    review.reviews = processed_reviews

    # Set other collection attributes
    review.revision_history.extend(content.get("revision_history", []))
    review.metrics_results = content.get("metrics_results", {})
    review.consensus_result = content.get("consensus_result", {})

    # Handle timestamps
    if "created_at" in content and isinstance(content["created_at"], str):
        try:
            review.created_at = datetime.fromisoformat(content["created_at"])
        except ValueError:
            logger.warning(f"Invalid created_at timestamp: {content['created_at']}")

    if "updated_at" in content and isinstance(content["updated_at"], str):
        try:
            review.updated_at = datetime.fromisoformat(content["updated_at"])
        except ValueError:
            logger.warning(f"Invalid updated_at timestamp: {content['updated_at']}")

    # Handle previous_review reference if available
    if "previous_review" in content and content["previous_review"]:
        previous_review_id = None
        if isinstance(content["previous_review"], dict):
            previous_review_id = content["previous_review"].get("review_id")
        elif isinstance(content["previous_review"], str):
            previous_review_id = content["previous_review"]

        if previous_review_id:
            # Set a placeholder that can be resolved later if needed
            review.previous_review = {"review_id": previous_review_id}

    # Set up memory_manager if available in the current context
    # This is important for subsequent memory operations
    try:
        from devsynth.application.memory.memory_manager import get_memory_manager

        memory_manager = get_memory_manager()
        if memory_manager:
            review.memory_manager = memory_manager
    except (ImportError, Exception) as e:
        logger.debug(f"Could not set memory_manager on review: {e}")

    # Set other optional attributes if present
    if "acceptance_criteria" in content:
        review.acceptance_criteria = content.get("acceptance_criteria")

    if "quality_metrics" in content:
        review.quality_metrics = content.get("quality_metrics")

    if "revision" in content:
        review.revision = content.get("revision")

    # Handle team reference if available
    if "team" in content and content["team"]:
        team_data = content["team"]
        if isinstance(team_data, dict) and "name" in team_data:
            # This is a placeholder for team reconstruction
            # In a real implementation, you might want to load the team from a registry
            review.team = team_data

    return review


def store_collaboration_entity(
    memory_manager: Any,
    entity: Any,
    primary_store: str = "tinydb",
    immediate_sync: bool = False,
    transaction_id: str | None = None,
    memory_item: MemoryItem | None = None,
) -> str:
    """
    Store a collaboration entity in memory with optional cross-store synchronization.

    This function has enhanced handling for different store types and transaction management
    to ensure consistent state across stores.

    Args:
        memory_manager: The memory manager to use
        entity: The collaboration entity to store
        primary_store: The primary store to use
        immediate_sync: Whether to synchronize immediately or queue for later
        transaction_id: Optional transaction ID for atomic operations
        memory_item: Optional pre-converted memory item to avoid redundant conversion

    Returns:
        The ID of the stored entity
    """
    # Get entity ID for logging
    entity_id = _resolve_entity_id(entity)

    # Check if memory_manager is valid
    if not memory_manager:
        logger.error(f"Invalid memory manager provided for entity {entity_id}")
        return entity_id

    # Check if memory_manager has adapters
    if not hasattr(memory_manager, "adapters") or not memory_manager.adapters:
        logger.error(f"Memory manager has no adapters for entity {entity_id}")
        return entity_id

    # Validate primary store exists
    available_stores = list(memory_manager.adapters.keys())
    if primary_store not in available_stores and available_stores:
        logger.warning(
            f"Primary store '{primary_store}' not available. Using {available_stores[0]} instead."
        )
        primary_store = available_stores[0]

    # Check if we have a sync manager for transactions
    has_sync_manager = hasattr(memory_manager, "sync_manager")

    # Convert to memory item if not provided
    if memory_item is None:
        try:
            # Determine the memory type based on the entity type
            if isinstance(entity, CollaborationTask):
                memory_type = MemoryType.COLLABORATION_TASK
            elif isinstance(entity, AgentMessage):
                memory_type = MemoryType.COLLABORATION_MESSAGE
            elif PeerReview is not None and isinstance(entity, PeerReview):
                memory_type = MemoryType.PEER_REVIEW
            else:
                memory_type = _get_memory_type_for_entity(entity)

            # Convert to memory item
            memory_item = to_memory_item(entity, memory_type)
        except Exception as e:
            logger.error(f"Failed to convert entity {entity_id} to memory item: {e}")
            return entity_id

    # Check if we need to start a transaction
    transaction_started = False
    if transaction_id is None and has_sync_manager:
        try:
            transaction_id = f"collab_{memory_item.id}_{datetime.now().timestamp()}"
            memory_manager.sync_manager.begin_transaction(transaction_id)
            transaction_started = True
            logger.debug(
                f"Started transaction {transaction_id} for entity {memory_item.id}"
            )
        except Exception as e:
            logger.warning(f"Failed to start transaction: {e}")
            # Continue without transaction if it fails

    try:
        # Handle different store types
        if primary_store == "kuzu" and "kuzu" in memory_manager.adapters:
            _store_in_kuzu(memory_manager, memory_item, immediate_sync)
        elif primary_store == "graph" and "graph" in memory_manager.adapters:
            _store_in_graph(memory_manager, memory_item, immediate_sync)
        else:
            # Standard behavior for other stores
            if immediate_sync:
                memory_manager.update_item(primary_store, memory_item)
            else:
                memory_manager.queue_update(primary_store, memory_item)

        # Synchronize to any additional stores for redundancy
        other_stores = [
            name for name in memory_manager.adapters.keys() if name != primary_store
        ]
        for store_name in other_stores:
            try:
                if immediate_sync:
                    memory_manager.update_item(store_name, memory_item)
                else:
                    memory_manager.queue_update(store_name, memory_item)
                logger.debug(
                    f"Synchronized entity {memory_item.id} to store {store_name}"
                )
            except Exception as sync_error:
                logger.warning(
                    f"Failed to sync entity {memory_item.id} to store {store_name}: {sync_error}"
                )

        # If we started a transaction, commit it
        if transaction_started and transaction_id and has_sync_manager:
            try:
                memory_manager.sync_manager.commit_transaction(transaction_id)
                logger.debug(
                    f"Committed transaction {transaction_id} for entity {memory_item.id}"
                )
            except Exception as e:
                logger.warning(f"Failed to commit transaction {transaction_id}: {e}")
                # We don't rollback here since the operation might have succeeded

        result_id = str(memory_item.id)
        return result_id

    except Exception as e:
        logger.error(f"Error storing entity {memory_item.id}: {e}")

        # If we started a transaction, roll it back
        if transaction_started and transaction_id and has_sync_manager:
            try:
                memory_manager.sync_manager.rollback_transaction(transaction_id)
                logger.debug(f"Rolled back transaction {transaction_id} due to error")
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction {transaction_id}: {rollback_error}"
                )

        # Re-raise the exception
        raise


def _store_in_kuzu(
    memory_manager: Any, memory_item: MemoryItem, immediate_sync: bool
) -> None:
    """
    Store a memory item in a Kuzu store with special handling.

    Args:
        memory_manager: The memory manager to use
        memory_item: The memory item to store
        immediate_sync: Whether to synchronize immediately or queue for later
    """
    try:
        # Get the Kuzu adapter
        kuzu_adapter = memory_manager.adapters["kuzu"]

        # Check if the adapter has a transaction method
        if hasattr(kuzu_adapter, "transaction"):
            with kuzu_adapter.transaction():
                if immediate_sync:
                    memory_manager.update_item("kuzu", memory_item)
                else:
                    memory_manager.queue_update("kuzu", memory_item)
        else:
            # No transaction support, proceed normally
            if immediate_sync:
                memory_manager.update_item("kuzu", memory_item)
            else:
                memory_manager.queue_update("kuzu", memory_item)

        # Also store in a fallback store for redundancy
        if "tinydb" in memory_manager.adapters:
            try:
                memory_manager.queue_update("tinydb", memory_item)
            except Exception as e:
                logger.warning(f"Failed to store in fallback tinydb: {e}")

    except Exception as e:
        logger.warning(f"Error with Kuzu store, falling back to default: {e}")
        # Fall back to default behavior
        if "tinydb" in memory_manager.adapters:
            if immediate_sync:
                memory_manager.update_item("tinydb", memory_item)
            else:
                memory_manager.queue_update("tinydb", memory_item)
        else:
            # If tinydb is not available, try the first available store
            available_stores = list(memory_manager.adapters.keys())
            if available_stores:
                if immediate_sync:
                    memory_manager.update_item(available_stores[0], memory_item)
                else:
                    memory_manager.queue_update(available_stores[0], memory_item)
            else:
                raise ValueError("No available stores for fallback")


def _store_in_graph(
    memory_manager: Any, memory_item: MemoryItem, immediate_sync: bool
) -> None:
    """
    Store a memory item in a Graph store with special handling.

    Args:
        memory_manager: The memory manager to use
        memory_item: The memory item to store
        immediate_sync: Whether to synchronize immediately or queue for later
    """
    try:
        # Get the Graph adapter
        graph_adapter = memory_manager.adapters["graph"]

        # Store in the graph store
        if immediate_sync:
            memory_manager.update_item("graph", memory_item)
        else:
            memory_manager.queue_update("graph", memory_item)

        # Also store in a fallback store for redundancy
        if "tinydb" in memory_manager.adapters:
            try:
                memory_manager.queue_update("tinydb", memory_item)
            except Exception as e:
                logger.warning(f"Failed to store in fallback tinydb: {e}")

    except Exception as e:
        logger.warning(f"Error with Graph store, falling back to default: {e}")
        # Fall back to default behavior
        if "tinydb" in memory_manager.adapters:
            if immediate_sync:
                memory_manager.update_item("tinydb", memory_item)
            else:
                memory_manager.queue_update("tinydb", memory_item)
        else:
            # If tinydb is not available, try the first available store
            available_stores = list(memory_manager.adapters.keys())
            if available_stores:
                if immediate_sync:
                    memory_manager.update_item(available_stores[0], memory_item)
                else:
                    memory_manager.queue_update(available_stores[0], memory_item)
            else:
                raise ValueError("No available stores for fallback")


def retrieve_collaboration_entity(
    memory_manager: Any, entity_id: str, entity_type: type[Any] | None = None
) -> Any:
    """
    Retrieve a collaboration entity from memory.

    Args:
        memory_manager: The memory manager to use
        entity_id: The ID of the entity to retrieve
        entity_type: Optional type hint for the entity

    Returns:
        The retrieved entity, or None if not found
    """
    # Retrieve the memory item
    memory_item = memory_manager.retrieve(entity_id)
    if not memory_item:
        return None

    # Convert to entity
    entity = from_memory_item(memory_item)

    # Verify type if specified
    if entity_type is not None and not isinstance(entity, entity_type):
        logger.warning(
            f"Retrieved entity {entity_id} is not of expected type {entity_type}"
        )
        return None

    return entity


def store_with_retry(
    memory_manager: Any,
    entity: Any,
    primary_store: str = "tinydb",
    immediate_sync: bool = False,
    max_retries: int = 3,
    transaction_id: str | None = None,
    ensure_cross_store_sync: bool = True,
) -> str:
    """
    Store a collaboration entity with enhanced retry logic and cross-store synchronization.

    This function has improved error handling and ensures data consistency across
    different memory stores.

    Args:
        memory_manager: The memory manager to use
        entity: The collaboration entity to store
        primary_store: The primary store to use
        immediate_sync: Whether to synchronize immediately or queue for later
        max_retries: Maximum number of retry attempts
        transaction_id: Optional transaction ID for atomic operations
        ensure_cross_store_sync: Whether to ensure cross-store synchronization

    Returns:
        The ID of the stored entity
    """
    import time

    # Get entity ID for logging and fallback
    entity_id = _resolve_entity_id(entity)

    # Determine available stores for cross-store synchronization
    available_stores = []
    if hasattr(memory_manager, "adapters"):
        available_stores = list(memory_manager.adapters.keys())

    # Validate primary store exists
    if primary_store not in available_stores and available_stores:
        logger.warning(
            f"Primary store '{primary_store}' not available. Using {available_stores[0]} instead."
        )
        primary_store = available_stores[0]

    # Check if we have a sync manager for transactions
    has_sync_manager = hasattr(memory_manager, "sync_manager")

    # Start a transaction if one isn't already in progress and we have a sync manager
    transaction_started = False
    if transaction_id is None and has_sync_manager:
        try:
            transaction_id = f"store_retry_{entity_id}_{datetime.now().timestamp()}"
            memory_manager.sync_manager.begin_transaction(transaction_id)
            transaction_started = True
            logger.debug(f"Started transaction {transaction_id} for entity {entity_id}")
        except Exception as e:
            logger.warning(f"Failed to start transaction: {e}")
            # Continue without transaction if it fails

    # Prepare memory item once to avoid repeated conversions
    try:
        memory_type = _get_memory_type_for_entity(entity)
        memory_item = to_memory_item(entity, memory_type)
    except Exception as e:
        logger.error(f"Failed to convert entity {entity_id} to memory item: {e}")
        if transaction_started and transaction_id and has_sync_manager:
            try:
                memory_manager.sync_manager.rollback_transaction(transaction_id)
                logger.debug(
                    f"Rolled back transaction {transaction_id} due to conversion error"
                )
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction {transaction_id}: {rollback_error}"
                )
        return entity_id  # Return ID as fallback

    try:
        # Main retry loop
        retries = 0
        last_error = None
        success = False
        sync_failures: list[tuple[str, str]] = []

        while retries < max_retries and not success:
            try:
                # Store in primary store
                if immediate_sync:
                    memory_manager.update_item(primary_store, memory_item)
                else:
                    memory_manager.queue_update(primary_store, memory_item)

                # Mark primary store operation as successful
                success = True
                logger.debug(
                    f"Successfully stored entity {entity_id} in {primary_store}"
                )

                # If cross-store sync is requested and we have multiple stores
                if ensure_cross_store_sync and len(available_stores) > 1:
                    sync_failures.clear()  # Track any sync failures

                    # Try to store in other available stores for redundancy
                    for store_name in available_stores:
                        if store_name != primary_store:
                            try:
                                # Use update_item for critical data to ensure it's stored
                                if immediate_sync:
                                    memory_manager.update_item(store_name, memory_item)
                                else:
                                    memory_manager.queue_update(store_name, memory_item)
                                logger.debug(
                                    f"Synchronized entity {entity_id} to store {store_name}"
                                )
                            except Exception as sync_error:
                                sync_failures.append((store_name, str(sync_error)))
                                logger.warning(
                                    f"Failed to sync entity {entity_id} to store {store_name}: {sync_error}"
                                )

                    # If we had sync failures but primary succeeded, log a warning
                    if sync_failures:
                        logger.warning(
                            f"Entity {entity_id} stored in primary store {primary_store} but "
                            f"failed to sync to {len(sync_failures)} other stores"
                        )

                # If everything succeeded, commit the transaction
                if (
                    success
                    and transaction_started
                    and transaction_id
                    and has_sync_manager
                ):
                    try:
                        memory_manager.sync_manager.commit_transaction(transaction_id)
                        logger.debug(
                            f"Committed transaction {transaction_id} for entity {entity_id}"
                        )
                    except Exception as commit_error:
                        logger.warning(
                            f"Failed to commit transaction {transaction_id}: {commit_error}"
                        )
                        # We don't rollback here since the operations succeeded
                # Attempt to flush any queued updates so hooks fire promptly
                try:
                    if hasattr(memory_manager, "flush_updates"):
                        memory_manager.flush_updates()
                except Exception as flush_error:  # pragma: no cover - best effort
                    logger.debug(
                        f"Failed to flush updates after storing entity {entity_id}: {flush_error}"
                    )

                # Return the entity ID
                return entity_id

            except Exception as e:
                last_error = e
                retries += 1

                if retries >= max_retries:
                    logger.error(
                        f"Failed to store entity {entity_id} after {max_retries} attempts: {e}"
                    )
                    break

                # Exponential backoff with jitter
                base_wait_time = 0.1 * (2**retries)
                jitter = 0.1 * base_wait_time * (0.5 - random.random())  # +/- 5% jitter
                wait_time = max(0.1, base_wait_time + jitter)

                logger.warning(
                    f"Retry {retries}/{max_retries} for entity {entity_id} after error: {e}. "
                    f"Waiting {wait_time:.2f}s before retry."
                )

                time.sleep(wait_time)

        # If we get here, all retries failed for the primary store

        # If we started a transaction, roll it back
        if transaction_started and transaction_id and has_sync_manager:
            try:
                memory_manager.sync_manager.rollback_transaction(transaction_id)
                logger.debug(
                    f"Rolled back transaction {transaction_id} due to primary store failure"
                )
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction {transaction_id}: {rollback_error}"
                )

        # Try fallback stores in order of preference
        fallback_stores = [
            s
            for s in ["tinydb", "graph", "kuzu"]
            if s in available_stores and s != primary_store
        ]

        for fallback_store in fallback_stores:
            try:
                logger.warning(
                    f"Attempting fallback to {fallback_store} for entity {entity_id}"
                )
                memory_manager.update_item(fallback_store, memory_item)
                logger.info(
                    f"Successfully stored entity {entity_id} in fallback store {fallback_store}"
                )
                try:
                    if hasattr(memory_manager, "flush_updates"):
                        memory_manager.flush_updates()
                except Exception as flush_error:  # pragma: no cover - defensive
                    logger.debug(
                        f"Failed to flush updates after fallback store {fallback_store} for entity {entity_id}: {flush_error}"
                    )
                return entity_id
            except Exception as fallback_error:
                logger.warning(
                    f"Fallback to {fallback_store} failed for entity {entity_id}: {fallback_error}"
                )

        # All attempts failed, return the entity ID as a last resort
        logger.error(f"All storage attempts failed for entity {entity_id}")
        return entity_id

    except Exception as outer_error:
        # Catch any unexpected errors in our retry logic
        logger.error(
            f"Unexpected error in store_with_retry for entity {entity_id}: {outer_error}"
        )

        # If we started a transaction, roll it back
        if transaction_started and transaction_id and has_sync_manager:
            try:
                memory_manager.sync_manager.rollback_transaction(transaction_id)
                logger.debug(
                    f"Rolled back transaction {transaction_id} due to unexpected error"
                )
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction {transaction_id}: {rollback_error}"
                )

        # Return the entity ID as a last resort
        return entity_id


def _get_memory_type_for_entity(entity: Any) -> MemoryType:
    """
    Determine the memory type for an entity.

    Args:
        entity: The entity to determine the memory type for

    Returns:
        The appropriate memory type for the entity
    """
    if isinstance(entity, CollaborationTask):
        return MemoryType.COLLABORATION_TASK
    elif isinstance(entity, AgentMessage):
        return MemoryType.COLLABORATION_MESSAGE
    elif PeerReview is not None and isinstance(entity, PeerReview):
        return MemoryType.PEER_REVIEW
    else:
        # Default to a generic type
        return MemoryType.LONG_TERM
