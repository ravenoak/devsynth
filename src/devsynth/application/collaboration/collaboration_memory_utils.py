"""
Utility functions for integrating collaboration entities with the memory system.

This module provides serialization/deserialization methods for collaboration entities
to convert between domain objects and memory items.
"""

import json
import random
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type, Union, cast

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger

from .agent_collaboration import AgentMessage, CollaborationTask, TaskStatus

# Use TYPE_CHECKING for type hints to avoid circular imports
if TYPE_CHECKING:
    from .peer_review import PeerReview

logger = DevSynthLogger(__name__)


def flush_memory_queue(memory_manager: Any) -> List[tuple[str, MemoryItem]]:
    """Flush queued memory updates and return flushed items.

    This helper captures the current sync queue, performs a flush, and returns
    the queued operations so callers may requeue them if a rollback is needed.

    Args:
        memory_manager: The memory manager instance coordinating updates.

    Returns:
        List of ``(store, MemoryItem)`` tuples that were flushed.
    """

    if not memory_manager or not hasattr(memory_manager, "sync_manager"):
        return []
    queue: List[tuple[str, MemoryItem]] = list(
        getattr(memory_manager.sync_manager, "_queue", [])
    )
    try:
        if hasattr(memory_manager, "flush_updates"):
            memory_manager.flush_updates()
    except Exception:  # pragma: no cover - defensive
        logger.debug("Flush failed", exc_info=True)
    return queue


def restore_memory_queue(
    memory_manager: Any, queued_items: List[tuple[str, MemoryItem]]
) -> None:
    """Requeue memory updates previously returned by :func:`flush_memory_queue`.

    Args:
        memory_manager: The memory manager handling updates.
        queued_items: Items to requeue in their original order.
    """

    if not memory_manager or not queued_items:
        return
    for store, item in queued_items:
        try:
            memory_manager.queue_update(store, item)
        except Exception:  # pragma: no cover - best effort
            logger.debug("Requeue failed", exc_info=True)


def to_memory_item(entity: Any, memory_type: MemoryType) -> MemoryItem:
    """
    Convert a collaboration entity to a memory item.

    Args:
        entity: The collaboration entity to convert
        memory_type: The type of memory to store the entity as

    Returns:
        A MemoryItem representing the entity
    """
    # Import here to avoid circular imports
    from .peer_review import PeerReview

    if not entity:
        raise ValueError("Cannot convert None to MemoryItem")

    # Get entity ID
    entity_id = getattr(entity, "id", None) or getattr(entity, "review_id", None)
    if not entity_id:
        raise ValueError(f"Entity {entity} does not have an id attribute")

    # Get entity content
    if hasattr(entity, "to_dict"):
        content = entity.to_dict()
    else:
        # Try to convert to dict using __dict__
        try:
            content = entity.__dict__.copy()
            # Remove any attributes that can't be serialized
            for key in list(content.keys()):
                if key.startswith("_") or callable(content[key]):
                    content.pop(key)
        except (AttributeError, TypeError):
            raise ValueError(f"Entity {entity} cannot be converted to a dictionary")

    # Create metadata
    metadata = {
        "entity_type": entity.__class__.__name__,
        "created_at": datetime.now().isoformat(),
    }

    # Add additional metadata based on entity type
    if isinstance(entity, CollaborationTask):
        metadata["task_type"] = entity.task_type
        metadata["status"] = (
            entity.status.name if hasattr(entity.status, "name") else str(entity.status)
        )
        if entity.parent_task_id:
            metadata["parent_task_id"] = entity.parent_task_id
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
    elif isinstance(entity, PeerReview):
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
    content = item.content

    # Convert status string to TaskStatus enum
    status_str = content.get("status")
    if isinstance(status_str, str):
        try:
            status = TaskStatus[status_str]
        except KeyError:
            logger.warning(f"Unknown task status: {status_str}")
            status = TaskStatus.PENDING
    else:
        status = content.get("status", TaskStatus.PENDING)

    # Create the task
    task = CollaborationTask(
        task_type=content.get("task_type", ""),
        description=content.get("description", ""),
        inputs=content.get("inputs", {}),
        required_capabilities=content.get("required_capabilities", []),
        parent_task_id=content.get("parent_task_id"),
        priority=content.get("priority", 1),
    )

    # Set additional attributes
    task.id = item.id
    task.status = status
    task.assigned_agent_id = content.get("assigned_agent_id")
    task.result = content.get("result")

    # Handle timestamps
    if "created_at" in content and isinstance(content["created_at"], str):
        try:
            task.created_at = datetime.fromisoformat(content["created_at"])
        except ValueError:
            logger.warning(f"Invalid created_at timestamp: {content['created_at']}")

    if "updated_at" in content and isinstance(content["updated_at"], str):
        try:
            task.updated_at = datetime.fromisoformat(content["updated_at"])
        except ValueError:
            logger.warning(f"Invalid updated_at timestamp: {content['updated_at']}")

    if (
        "started_at" in content
        and content["started_at"]
        and isinstance(content["started_at"], str)
    ):
        try:
            task.started_at = datetime.fromisoformat(content["started_at"])
        except ValueError:
            logger.warning(f"Invalid started_at timestamp: {content['started_at']}")

    if (
        "completed_at" in content
        and content["completed_at"]
        and isinstance(content["completed_at"], str)
    ):
        try:
            task.completed_at = datetime.fromisoformat(content["completed_at"])
        except ValueError:
            logger.warning(f"Invalid completed_at timestamp: {content['completed_at']}")

    # Handle relationships
    task.subtasks = []  # These will be loaded separately
    task.dependencies = content.get("dependencies", [])
    task.messages = []  # These will be loaded separately

    return task


def _memory_item_to_message(item: MemoryItem) -> AgentMessage:
    """Convert a memory item to an AgentMessage."""
    content = item.content

    # Convert message_type string to MessageType enum
    from .agent_collaboration import MessageType

    message_type_str = content.get("message_type")
    if isinstance(message_type_str, str):
        try:
            message_type = MessageType[message_type_str]
        except KeyError:
            logger.warning(f"Unknown message type: {message_type_str}")
            message_type = MessageType.STATUS_UPDATE
    else:
        message_type = content.get("message_type", MessageType.STATUS_UPDATE)

    # Create the message
    message = AgentMessage(
        sender_id=content.get("sender_id", ""),
        recipient_id=content.get("recipient_id", ""),
        message_type=message_type,
        content=content.get("content", {}),
        related_task_id=content.get("related_task_id"),
    )

    # Set additional attributes
    message.id = item.id

    # Handle timestamp
    if "timestamp" in content and isinstance(content["timestamp"], str):
        try:
            message.timestamp = datetime.fromisoformat(content["timestamp"])
        except ValueError:
            logger.warning(f"Invalid timestamp: {content['timestamp']}")

    return message


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

    from .peer_review import PeerReview

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
    processed_reviewers = []
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
    review = PeerReview(
        work_product=content.get("work_product", {}),
        author=author,
        reviewers=processed_reviewers,
    )

    # Set the review_id
    review.review_id = item.id

    # Set additional attributes
    review.status = content.get("status", "pending")
    review.quality_score = content.get("quality_score", 0.0)

    # Handle reviews dictionary - keys might be agent objects
    reviews_dict = content.get("reviews", {})
    processed_reviews = {}
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
    review.revision_history = content.get("revision_history", [])
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
    transaction_id: Optional[str] = None,
    memory_item: Optional[MemoryItem] = None,
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
    entity_id = getattr(entity, "id", None) or getattr(
        entity, "review_id", str(id(entity))
    )

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
            # Import here to avoid circular imports
            from .peer_review import PeerReview

            # Determine the memory type based on the entity type
            if isinstance(entity, CollaborationTask):
                memory_type = MemoryType.COLLABORATION_TASK
            elif isinstance(entity, AgentMessage):
                memory_type = MemoryType.COLLABORATION_MESSAGE
            elif isinstance(entity, PeerReview):
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

        return memory_item.id

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
    memory_manager: Any, entity_id: str, entity_type: Type = None
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
    if entity_type and not isinstance(entity, entity_type):
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
    transaction_id: Optional[str] = None,
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
    entity_id = getattr(entity, "id", None) or getattr(
        entity, "review_id", str(id(entity))
    )

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
        sync_failures = []

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
                    sync_failures = []  # Track any sync failures

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
    # Import here to avoid circular imports
    from .peer_review import PeerReview

    if isinstance(entity, CollaborationTask):
        return MemoryType.COLLABORATION_TASK
    elif isinstance(entity, AgentMessage):
        return MemoryType.COLLABORATION_MESSAGE
    elif isinstance(entity, PeerReview):
        return MemoryType.PEER_REVIEW
    else:
        # Default to a generic type
        return MemoryType.LONG_TERM
