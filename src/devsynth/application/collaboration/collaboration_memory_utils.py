"""
Utility functions for integrating collaboration entities with the memory system.

This module provides serialization/deserialization methods for collaboration entities
to convert between domain objects and memory items.
"""

from typing import Any, Dict, List, Optional, Union, Type, cast, TYPE_CHECKING
import json
from datetime import datetime

from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.logging_setup import DevSynthLogger
from .agent_collaboration import CollaborationTask, AgentMessage, TaskStatus

# Use TYPE_CHECKING for type hints to avoid circular imports
if TYPE_CHECKING:
    from .peer_review import PeerReview

logger = DevSynthLogger(__name__)


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
        "created_at": datetime.now().isoformat()
    }
    
    # Add additional metadata based on entity type
    if isinstance(entity, CollaborationTask):
        metadata["task_type"] = entity.task_type
        metadata["status"] = entity.status.name if hasattr(entity.status, "name") else str(entity.status)
        if entity.parent_task_id:
            metadata["parent_task_id"] = entity.parent_task_id
    elif isinstance(entity, AgentMessage):
        metadata["message_type"] = entity.message_type.name if hasattr(entity.message_type, "name") else str(entity.message_type)
        metadata["sender_id"] = entity.sender_id
        metadata["recipient_id"] = entity.recipient_id
        if entity.related_task_id:
            metadata["related_task_id"] = entity.related_task_id
    elif isinstance(entity, PeerReview):
        metadata["status"] = entity.status
        metadata["author_id"] = getattr(entity.author, "id", str(entity.author))
        metadata["quality_score"] = entity.quality_score
    
    return MemoryItem(
        id=entity_id,
        content=content,
        memory_type=memory_type,
        metadata=metadata
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
        priority=content.get("priority", 1)
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
    
    if "started_at" in content and content["started_at"] and isinstance(content["started_at"], str):
        try:
            task.started_at = datetime.fromisoformat(content["started_at"])
        except ValueError:
            logger.warning(f"Invalid started_at timestamp: {content['started_at']}")
    
    if "completed_at" in content and content["completed_at"] and isinstance(content["completed_at"], str):
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
        related_task_id=content.get("related_task_id")
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
    """Convert a memory item to a PeerReview."""
    # Import here to avoid circular imports
    from .peer_review import PeerReview
    
    content = item.content
    
    # Create a minimal PeerReview object
    # Note: This is a simplified conversion that doesn't fully reconstruct the PeerReview
    # For a complete reconstruction, we would need to load the author, reviewers, etc.
    review = PeerReview(
        work_product=content.get("work_product", {}),
        author=content.get("author", ""),
        reviewers=content.get("reviewers", [])
    )
    
    # Set the review_id
    review.review_id = item.id
    
    # Set additional attributes
    review.status = content.get("status", "pending")
    review.quality_score = content.get("quality_score", 0.0)
    review.reviews = content.get("reviews", {})
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
    
    return review


def store_collaboration_entity(
    memory_manager: Any,
    entity: Any,
    primary_store: str = "tinydb",
    immediate_sync: bool = False
) -> str:
    """
    Store a collaboration entity in memory with optional cross-store synchronization.
    
    Args:
        memory_manager: The memory manager to use
        entity: The collaboration entity to store
        primary_store: The primary store to use
        immediate_sync: Whether to synchronize immediately or queue for later
        
    Returns:
        The ID of the stored entity
    """
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
        raise ValueError(f"Unsupported entity type: {type(entity)}")
    
    # Convert to memory item
    memory_item = to_memory_item(entity, memory_type)
    
    # Store in memory
    if immediate_sync:
        # Immediate synchronization
        memory_manager.update_item(primary_store, memory_item)
    else:
        # Queue for later synchronization
        memory_manager.queue_update(primary_store, memory_item)
    
    return memory_item.id


def retrieve_collaboration_entity(
    memory_manager: Any,
    entity_id: str,
    entity_type: Type = None
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
        logger.warning(f"Retrieved entity {entity_id} is not of expected type {entity_type}")
        return None
    
    return entity


def store_with_retry(
    memory_manager: Any,
    entity: Any,
    primary_store: str = "tinydb",
    immediate_sync: bool = False,
    max_retries: int = 3
) -> str:
    """
    Store a collaboration entity with retry logic.
    
    Args:
        memory_manager: The memory manager to use
        entity: The collaboration entity to store
        primary_store: The primary store to use
        immediate_sync: Whether to synchronize immediately or queue for later
        max_retries: Maximum number of retry attempts
        
    Returns:
        The ID of the stored entity
    """
    import time
    
    retries = 0
    while retries < max_retries:
        try:
            return store_collaboration_entity(
                memory_manager, entity, primary_store, immediate_sync
            )
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"Failed to store entity after {max_retries} attempts: {e}")
                # Fall back to returning the entity ID without storing
                return getattr(entity, "id", None) or getattr(entity, "review_id", str(id(entity)))
            
            # Exponential backoff
            wait_time = 0.1 * (2 ** retries)
            time.sleep(wait_time)