"""Multi-agent collaboration framework for DevSynth."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from collections.abc import Callable, Iterable

from devsynth.domain.interfaces.agent import Agent
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.logging_setup import DevSynthLogger

from .dto import (
    AgentPayload,
    CollaborationPayloadInput,
    JSONValue,
    MemorySyncPort,
    TaskDescriptor,
    ensure_collaboration_payload,
    ensure_memory_sync_port,
    serialize_memory_sync_port,
)

logger = DevSynthLogger(__name__)


class MessageType(Enum):
    """Types of messages that can be exchanged between agents."""

    TASK_ASSIGNMENT = auto()
    TASK_RESULT = auto()
    QUESTION = auto()
    ANSWER = auto()
    FEEDBACK = auto()
    SUGGESTION = auto()
    STATUS_UPDATE = auto()
    ERROR = auto()


class TaskStatus(Enum):
    """Status of a task in the collaboration system."""

    PENDING = auto()
    ASSIGNED = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    BLOCKED = auto()


def _ensure_agent_payload(content: CollaborationPayloadInput) -> AgentPayload:
    """Normalize arbitrary message content into an :class:`AgentPayload`."""

    if isinstance(content, AgentPayload):
        return content

    try:
        payload = ensure_collaboration_payload(content, default=AgentPayload)
    except TypeError:
        payload = AgentPayload(payload=content if content is not None else None)

    if isinstance(payload, AgentPayload):
        return payload

    return AgentPayload.from_dict(payload.to_dict())


def _sorted_mapping(items: Iterable[tuple[str, JSONValue]]) -> dict[str, JSONValue]:
    return dict(sorted(items, key=lambda pair: pair[0]))


def _coerce_datetime(value: Any) -> datetime | None:
    """Convert ISO strings into :class:`datetime` objects when possible."""

    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            logger.debug("Failed to parse datetime %s", value)
    return None


@dataclass(slots=True)
class AgentMessage:
    """A message exchanged between agents in the collaboration system."""

    sender_id: str
    recipient_id: str
    message_type: MessageType
    payload: AgentPayload
    related_task_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        self.payload = _ensure_agent_payload(self.payload)
        if isinstance(self.timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(self.timestamp)
            except ValueError:
                self.timestamp = datetime.now()

    @property
    def content(self) -> JSONValue:
        """Return a simplified view of the payload for backward compatibility."""

        if self.payload.attributes:
            return _sorted_mapping(tuple(self.payload.attributes.items()))
        if self.payload.payload is not None:
            return self.payload.payload
        if self.payload.summary is not None:
            return {"summary": self.payload.summary}
        return self.payload.to_dict()

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert the message to a dictionary."""

        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message_type": self.message_type.name,
            "content": self.payload.to_dict(),
            "related_task_id": self.related_task_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentMessage:
        message_type = data.get("message_type", MessageType.STATUS_UPDATE)
        if isinstance(message_type, str):
            try:
                message_type = MessageType[message_type]
            except KeyError:
                message_type = MessageType.STATUS_UPDATE

        payload_data = data.get("payload") or data.get("content", {})
        payload = _ensure_agent_payload(payload_data)

        timestamp_value = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_value)
            if isinstance(timestamp_value, str)
            else timestamp_value or datetime.now()
        )

        return cls(
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id", ""),
            message_type=message_type,
            payload=payload,
            related_task_id=data.get("related_task_id"),
            id=data.get("id", str(uuid.uuid4())),
            timestamp=timestamp,
        )


@dataclass(slots=True)
class CollaborationTask:
    """A task that can be assigned to agents in the collaboration system."""

    task_type: str
    description: str
    inputs: dict[str, Any]
    required_capabilities: list[str] = field(default_factory=list)
    parent_task_id: str | None = None
    priority: int = 1
    descriptor: TaskDescriptor | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: str | None = None
    result: Any | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    subtasks: list[CollaborationTask] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    messages: list[AgentMessage] = field(default_factory=list)
    sync_port: MemorySyncPort | None = None

    def __post_init__(self) -> None:
        self.inputs = dict(self.inputs)
        self.required_capabilities = list(self.required_capabilities)
        self.dependencies = list(self.dependencies)
        self.subtasks = list(self.subtasks)
        self.messages = list(self.messages)
        self.created_at = _coerce_datetime(self.created_at) or datetime.now()
        self.updated_at = _coerce_datetime(self.updated_at) or datetime.now()
        self.started_at = _coerce_datetime(self.started_at)
        self.completed_at = _coerce_datetime(self.completed_at)
        self._sync_descriptor()

    def _sync_descriptor(self) -> None:
        descriptor = self.descriptor
        metadata: dict[str, JSONValue] = {}
        if descriptor:
            metadata.update(descriptor.metadata)

        sync_port_raw = metadata.pop("sync_port", None) or metadata.pop(
            "memory_sync_port", None
        )
        if self.sync_port is None and sync_port_raw is not None:
            self.sync_port = ensure_memory_sync_port(sync_port_raw)
        elif sync_port_raw is not None:
            self.sync_port = ensure_memory_sync_port(sync_port_raw)

        if self.sync_port is not None:
            metadata["sync_port"] = serialize_memory_sync_port(self.sync_port)

        metadata["priority"] = self.priority
        metadata["task_type"] = self.task_type
        metadata = _sorted_mapping(metadata.items())

        summary = (
            descriptor.summary
            if descriptor and descriptor.summary
            else self.description
        )
        description = (
            descriptor.description
            if descriptor and descriptor.description
            else self.description
        )
        status_value = (
            descriptor.status if descriptor and descriptor.status else self.status.name
        )
        assignee = (
            descriptor.assignee
            if descriptor and descriptor.assignee
            else self.assigned_agent_id
        )
        tags = descriptor.tags if descriptor else ()

        self.descriptor = TaskDescriptor(
            task_id=self.id,
            summary=summary,
            description=description,
            status=status_value,
            assignee=assignee,
            tags=tuple(tags),
            metadata=metadata,
        )
        self.description = description or ""

    def refresh_descriptor(self) -> None:
        """Synchronize the descriptor with the current task state."""

        self._sync_descriptor()

    def to_dict(self) -> dict[str, Any]:
        """Convert the task to a dictionary."""

        return {
            "id": self.id,
            "task_type": self.task_type,
            "description": self.description,
            "inputs": dict(self.inputs),
            "required_capabilities": list(self.required_capabilities),
            "parent_task_id": self.parent_task_id,
            "priority": self.priority,
            "status": self.status.name,
            "assigned_agent_id": self.assigned_agent_id,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "subtasks": [subtask.id for subtask in self.subtasks],
            "dependencies": list(self.dependencies),
            "messages": [message.id for message in self.messages],
            "descriptor": self.descriptor.to_dict(),
            "sync_port": serialize_memory_sync_port(self.sync_port),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CollaborationTask:
        descriptor_data = data.get("descriptor")
        descriptor = (
            TaskDescriptor.from_dict(descriptor_data)
            if isinstance(descriptor_data, dict)
            else None
        )

        status_value = data.get("status", TaskStatus.PENDING)
        if isinstance(status_value, str):
            try:
                status_value = TaskStatus[status_value]
            except KeyError:
                status_value = TaskStatus.PENDING

        sync_port = ensure_memory_sync_port(data.get("sync_port"))

        created_at = _coerce_datetime(data.get("created_at")) or datetime.now()
        updated_at = _coerce_datetime(data.get("updated_at")) or datetime.now()

        return cls(
            task_type=data.get("task_type", ""),
            description=data.get("description", ""),
            inputs=dict(data.get("inputs", {})),
            required_capabilities=list(data.get("required_capabilities", [])),
            parent_task_id=data.get("parent_task_id"),
            priority=int(data.get("priority", 1)),
            descriptor=descriptor,
            id=data.get("id", str(uuid.uuid4())),
            status=(
                status_value
                if isinstance(status_value, TaskStatus)
                else TaskStatus.PENDING
            ),
            assigned_agent_id=data.get("assigned_agent_id"),
            result=data.get("result"),
            created_at=created_at,
            updated_at=updated_at,
            started_at=_coerce_datetime(data.get("started_at")),
            completed_at=_coerce_datetime(data.get("completed_at")),
            dependencies=list(data.get("dependencies", [])),
            sync_port=sync_port,
        )

    def add_subtask(self, subtask: CollaborationTask) -> None:
        """Add a subtask to this task."""

        subtask.parent_task_id = self.id
        self.subtasks.append(subtask)

    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to this task."""

        if task_id not in self.dependencies:
            self.dependencies.append(task_id)

    def add_message(self, message: AgentMessage) -> None:
        """Add a message to this task."""

        self.messages.append(message)

    def update_status(self, status: TaskStatus) -> None:
        """Update the status of this task."""

        self.status = status
        self.updated_at = datetime.now()

        if status == TaskStatus.IN_PROGRESS and not self.started_at:
            self.started_at = datetime.now()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            self.completed_at = datetime.now()

        self.refresh_descriptor()


class AgentCollaborationSystem:
    """
    System for enabling collaboration between specialized agents.

    This class implements a flexible collaboration protocol that allows
    agents to work together on complex tasks through message passing,
    task delegation, and coordination mechanisms.
    """

    def __init__(self, memory_manager=None):
        """
        Initialize the agent collaboration system.

        Args:
            memory_manager: Optional memory manager for persistence and cross-store synchronization
        """
        self.agents = {}  # Dictionary of agents by agent_id
        self.teams = {}  # Dictionary of teams by team_id
        self.tasks = {}  # Dictionary of tasks by task_id
        self.messages = {}  # Dictionary of messages by message_id
        self.agent_capabilities = {}  # Dictionary mapping agent_id to capabilities
        self.task_handlers = {}  # Dictionary mapping task_type to handler function
        self.memory_manager = memory_manager  # Memory manager for persistence

    def register_agent(self, agent: Agent) -> str:
        """
        Register an agent with the collaboration system.

        Args:
            agent: The agent to register

        Returns:
            The ID of the registered agent
        """
        agent_id = getattr(agent, "id", str(uuid.uuid4()))
        self.agents[agent_id] = agent

        # Extract agent capabilities
        capabilities = getattr(agent, "capabilities", [])
        self.agent_capabilities[agent_id] = set(capabilities)

        logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")
        return agent_id

    def create_team(self, team_id: str, agent_ids: list[str]) -> WSDETeam:
        """
        Create a new team of agents.

        Args:
            team_id: ID for the new team
            agent_ids: IDs of agents to include in the team

        Returns:
            The created team
        """
        team = WSDETeam(name="AgentCollaborationTeam")

        # Add agents to the team
        for agent_id in agent_ids:
            if agent_id in self.agents:
                team.add_agent(self.agents[agent_id])

        # Assign roles
        team.assign_roles()

        # Store the team in memory if memory manager is available
        if self.memory_manager:
            try:
                # Create a serializable representation of the team
                team_data = {
                    "id": team_id,
                    "name": team.name,
                    "agent_ids": agent_ids,
                    "roles": {
                        agent.id: role
                        for agent, role in team.roles.items()
                        if hasattr(agent, "id")
                    },
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }

                # Create a memory item
                from devsynth.domain.models.memory import MemoryItem, MemoryType

                team_item = MemoryItem(
                    id=team_id,
                    content=team_data,
                    memory_type=MemoryType.COLLABORATION_TEAM,
                    metadata={"entity_type": "WSDETeam"},
                )

                # Store in memory
                self.memory_manager.update_item("tinydb", team_item)
                try:
                    self.memory_manager.flush_updates()
                except Exception:
                    pass
                logger.info(f"Stored team {team_id} in memory")
            except Exception as e:
                logger.error(f"Failed to store team {team_id} in memory: {e}")

        # Store the team in in-memory dictionary
        self.teams[team_id] = team

        logger.info(f"Created team {team_id} with {len(team.agents)} agents")
        return team

    def _get_team(self, team_id: str) -> WSDETeam | None:
        """
        Get a team by ID from memory or in-memory dictionary.

        Args:
            team_id: The ID of the team to get

        Returns:
            The team, or None if not found
        """
        # First check in-memory dictionary
        if team_id in self.teams:
            return self.teams[team_id]

        # Then check memory if memory manager is available
        if self.memory_manager:
            try:
                # Import MemoryType
                from devsynth.domain.models.memory import MemoryType

                # Retrieve from memory
                team_item = self.memory_manager.retrieve(team_id)
                if team_item and team_item.memory_type == MemoryType.COLLABORATION_TEAM:
                    # Create a new team
                    team_data = team_item.content
                    team = WSDETeam(
                        name=team_data.get("name", "AgentCollaborationTeam")
                    )

                    # Add agents to the team
                    for agent_id in team_data.get("agent_ids", []):
                        if agent_id in self.agents:
                            team.add_agent(self.agents[agent_id])

                    # Assign roles (or use stored roles if available)
                    if not team.roles and team_data.get("roles"):
                        # This is a simplified approach; in a real implementation,
                        # you would need to map role names to actual role objects
                        team.assign_roles()

                    # Cache in in-memory dictionary
                    self.teams[team_id] = team
                    return team
            except Exception as e:
                logger.error(f"Failed to retrieve team {team_id} from memory: {e}")

        return None

    def register_task_handler(
        self, task_type: str, handler: Callable[[CollaborationTask], dict[str, Any]]
    ) -> None:
        """
        Register a handler function for a specific task type.

        Args:
            task_type: The type of task
            handler: The function that handles tasks of this type
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    def create_task(
        self,
        task_type: str,
        description: str,
        inputs: dict[str, Any],
        required_capabilities: list[str] | None = None,
        parent_task_id: str | None = None,
        priority: int = 1,
        descriptor: Any | None = None,
    ) -> CollaborationTask:
        """
        Create a new task in the collaboration system.

        Args:
            task_type: Type of task
            description: Description of the task
            inputs: Input data for the task
            required_capabilities: Capabilities required to perform the task
            parent_task_id: ID of the parent task (if this is a subtask)
            priority: Priority of the task (higher values = higher priority)
            descriptor: Optional mapping or :class:`TaskDescriptor` to merge
                with the generated descriptor for the task.

        Returns:
            The created task
        """
        descriptor_obj: TaskDescriptor | None
        if descriptor is None:
            descriptor_obj = None
        elif isinstance(descriptor, TaskDescriptor):
            descriptor_obj = descriptor
        elif isinstance(descriptor, dict):
            descriptor_obj = TaskDescriptor.from_dict(descriptor)
        else:
            raise TypeError("descriptor must be TaskDescriptor or mapping")

        task = CollaborationTask(
            task_type=task_type,
            description=description,
            inputs=inputs,
            required_capabilities=required_capabilities or [],
            parent_task_id=parent_task_id,
            priority=priority,
            descriptor=descriptor_obj,
        )

        # Store task in memory if memory manager is available
        if self.memory_manager:
            try:
                from .collaboration_memory_utils import store_with_retry

                store_with_retry(
                    self.memory_manager,
                    task,
                    primary_store="tinydb",
                    immediate_sync=False,
                )
                logger.info(f"Stored task {task.id} in memory")
            except Exception as e:
                logger.error(f"Failed to store task {task.id} in memory: {e}")

        # Store task in in-memory dictionary
        self.tasks[task.id] = task

        # If this is a subtask, add it to the parent task
        if parent_task_id:
            # Get parent task from memory or in-memory dictionary
            parent_task = self._get_task(parent_task_id)
            if parent_task:
                parent_task.add_subtask(task)

                # Update parent task in memory if memory manager is available
                if self.memory_manager:
                    try:
                        from .collaboration_memory_utils import store_with_retry

                        store_with_retry(
                            self.memory_manager,
                            parent_task,
                            primary_store="tinydb",
                            immediate_sync=True,
                        )
                        logger.info(f"Updated parent task {parent_task_id} in memory")
                    except Exception as e:
                        logger.error(
                            f"Failed to update parent task {parent_task_id} in memory: {e}"
                        )

        logger.info(f"Created task {task.id} of type {task_type}")
        return task

    def _get_task(self, task_id: str) -> CollaborationTask | None:
        """
        Get a task by ID from memory or in-memory dictionary.

        Args:
            task_id: The ID of the task to get

        Returns:
            The task, or None if not found
        """
        # First check in-memory dictionary
        if task_id in self.tasks:
            return self.tasks[task_id]

        # Then check memory if memory manager is available
        if self.memory_manager:
            try:
                from .collaboration_memory_utils import retrieve_collaboration_entity

                task = retrieve_collaboration_entity(
                    self.memory_manager, task_id, entity_type=CollaborationTask
                )
                if task:
                    # Cache in in-memory dictionary
                    self.tasks[task_id] = task
                    return task
            except Exception as e:
                logger.error(f"Failed to retrieve task {task_id} from memory: {e}")

        return None

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        message_type: MessageType,
        content: Any,
        related_task_id: str | None = None,
    ) -> AgentMessage:
        """
        Send a message from one agent to another.

        Args:
            sender_id: ID of the sending agent
            recipient_id: ID of the receiving agent
            message_type: Type of message
            content: Content of the message. Supports dictionaries, strings,
                and collaboration DTO instances; the value is normalized into
                an :class:`AgentPayload`.
            related_task_id: ID of the task this message is related to (if any)

        Returns:
            The created message
        """
        payload = _ensure_agent_payload(content)
        message = AgentMessage(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            related_task_id=related_task_id,
        )

        # Store message in memory if memory manager is available
        if self.memory_manager:
            try:
                from .collaboration_memory_utils import store_with_retry

                store_with_retry(
                    self.memory_manager,
                    message,
                    primary_store="tinydb",
                    immediate_sync=False,
                )
                logger.info(f"Stored message {message.id} in memory")
            except Exception as e:
                logger.error(f"Failed to store message {message.id} in memory: {e}")

        # Store message in in-memory dictionary
        self.messages[message.id] = message

        # If this message is related to a task, add it to the task
        if related_task_id:
            # Get task from memory or in-memory dictionary
            task = self._get_task(related_task_id)
            if task:
                task.add_message(message)

                # Update task in memory if memory manager is available
                if self.memory_manager:
                    try:
                        from .collaboration_memory_utils import store_with_retry

                        store_with_retry(
                            self.memory_manager,
                            task,
                            primary_store="tinydb",
                            immediate_sync=True,
                        )
                        logger.info(
                            f"Updated task {related_task_id} in memory with message {message.id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to update task {related_task_id} in memory: {e}"
                        )

        logger.info(f"Sent message {message.id} from {sender_id} to {recipient_id}")
        return message

    def _get_message(self, message_id: str) -> AgentMessage | None:
        """
        Get a message by ID from memory or in-memory dictionary.

        Args:
            message_id: The ID of the message to get

        Returns:
            The message, or None if not found
        """
        # First check in-memory dictionary
        if message_id in self.messages:
            return self.messages[message_id]

        # Then check memory if memory manager is available
        if self.memory_manager:
            try:
                from .collaboration_memory_utils import retrieve_collaboration_entity

                message = retrieve_collaboration_entity(
                    self.memory_manager, message_id, entity_type=AgentMessage
                )
                if message:
                    # Cache in in-memory dictionary
                    self.messages[message_id] = message
                    return message
            except Exception as e:
                logger.error(
                    f"Failed to retrieve message {message_id} from memory: {e}"
                )

        return None

    def assign_task(self, task_id: str, agent_id: str | None = None) -> bool:
        """
        Assign a task to an agent.

        If agent_id is not provided, the system will automatically select
        the most appropriate agent based on capabilities and workload.

        Args:
            task_id: ID of the task to assign
            agent_id: ID of the agent to assign the task to (optional)

        Returns:
            True if the task was assigned successfully, False otherwise
        """
        # Get the task from memory or in-memory dictionary
        task = self._get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False

        # If the task is already assigned, return False
        if task.status != TaskStatus.PENDING:
            logger.error(f"Task {task_id} is already assigned or completed")
            return False

        # If agent_id is provided, assign the task to that agent
        if agent_id:
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                return False

            # Use a transaction if memory manager is available
            if self.memory_manager:
                try:
                    # Begin transaction
                    with self.memory_manager.begin_transaction(["tinydb", "graph"]):
                        # Update task
                        task.assigned_agent_id = agent_id
                        task.status = TaskStatus.ASSIGNED
                        task.updated_at = datetime.now()
                        task.refresh_descriptor()

                        # Store updated task in memory
                        from .collaboration_memory_utils import store_with_retry

                        store_with_retry(
                            self.memory_manager,
                            task,
                            primary_store="tinydb",
                            immediate_sync=True,
                        )

                        logger.info(
                            f"Assigned task {task_id} to agent {agent_id} (with transaction)"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to assign task {task_id} to agent {agent_id}: {e}"
                    )
                    return False
            else:
                # Update task in memory only
                task.assigned_agent_id = agent_id
                task.status = TaskStatus.ASSIGNED
                task.updated_at = datetime.now()
                task.refresh_descriptor()

            logger.info(f"Assigned task {task_id} to agent {agent_id}")
            return True

        # Otherwise, find the most appropriate agent
        best_agent_id = self._find_best_agent_for_task(task)

        if best_agent_id:
            # Use a transaction if memory manager is available
            if self.memory_manager:
                try:
                    # Begin transaction
                    with self.memory_manager.begin_transaction(["tinydb", "graph"]):
                        # Update task
                        task.assigned_agent_id = best_agent_id
                        task.status = TaskStatus.ASSIGNED
                        task.updated_at = datetime.now()
                        task.refresh_descriptor()

                        # Store updated task in memory
                        from .collaboration_memory_utils import store_with_retry

                        store_with_retry(
                            self.memory_manager,
                            task,
                            primary_store="tinydb",
                            immediate_sync=True,
                        )

                        logger.info(
                            f"Assigned task {task_id} to agent {best_agent_id} (with transaction)"
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to assign task {task_id} to agent {best_agent_id}: {e}"
                    )
                    return False
            else:
                # Update task in memory only
                task.assigned_agent_id = best_agent_id
                task.status = TaskStatus.ASSIGNED
                task.updated_at = datetime.now()
                task.refresh_descriptor()

            logger.info(f"Assigned task {task_id} to agent {best_agent_id}")
            return True

        logger.error(f"No suitable agent found for task {task_id}")
        return False

    def _find_best_agent_for_task(self, task: CollaborationTask) -> str | None:
        """
        Find the most appropriate agent for a task based on capabilities and workload.

        Args:
            task: The task to find an agent for

        Returns:
            The ID of the most appropriate agent, or None if no suitable agent was found
        """
        # Filter agents by required capabilities
        suitable_agents = []

        for agent_id, capabilities in self.agent_capabilities.items():
            # Check if the agent has all required capabilities
            if all(cap in capabilities for cap in task.required_capabilities):
                suitable_agents.append(agent_id)

        if not suitable_agents:
            return None

        # For now, just return the first suitable agent
        # In a more advanced implementation, we would consider workload, performance, etc.
        return suitable_agents[0]

    def execute_task(self, task_id: str) -> dict[str, Any]:
        """
        Execute a task using the assigned agent.

        Args:
            task_id: ID of the task to execute

        Returns:
            The result of the task execution
        """
        # Get the task from memory or in-memory dictionary
        task = self._get_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"success": False, "error": "Task not found"}

        # Check if the task is assigned
        if task.status != TaskStatus.ASSIGNED:
            logger.error(f"Task {task_id} is not assigned")
            return {"success": False, "error": "Task not assigned"}

        # Get the assigned agent
        agent_id = task.assigned_agent_id
        if agent_id not in self.agents:
            logger.error(f"Agent {agent_id} not found")
            return {"success": False, "error": "Agent not found"}

        agent = self.agents[agent_id]

        # Use a transaction if memory manager is available
        if self.memory_manager:
            try:
                # Begin transaction
                with self.memory_manager.begin_transaction(["tinydb", "graph"]):
                    # Update task status to IN_PROGRESS
                    task.update_status(TaskStatus.IN_PROGRESS)

                    # Store updated task in memory
                    from .collaboration_memory_utils import store_with_retry

                    store_with_retry(
                        self.memory_manager,
                        task,
                        primary_store="tinydb",
                        immediate_sync=True,
                    )

                    logger.info(
                        f"Updated task {task_id} status to IN_PROGRESS (with transaction)"
                    )
            except Exception as e:
                logger.error(
                    f"Failed to update task {task_id} status to IN_PROGRESS: {e}"
                )
                return {"success": False, "error": f"Failed to update task status: {e}"}
        else:
            # Update task status in memory only
            task.update_status(TaskStatus.IN_PROGRESS)

        try:
            # Check if there's a specific handler for this task type
            if task.task_type in self.task_handlers:
                handler = self.task_handlers[task.task_type]
                result = handler(task)
            else:
                # Otherwise, use the agent's process method
                result = agent.process(
                    {
                        "task_id": task.id,
                        "task_type": task.task_type,
                        "description": task.description,
                        "inputs": task.inputs,
                    }
                )

            # Use a transaction if memory manager is available
            if self.memory_manager:
                try:
                    # Begin transaction
                    with self.memory_manager.begin_transaction(["tinydb", "graph"]):
                        # Update task with result and status
                        task.result = result
                        task.update_status(TaskStatus.COMPLETED)

                        # Store updated task in memory
                        from .collaboration_memory_utils import store_with_retry

                        store_with_retry(
                            self.memory_manager,
                            task,
                            primary_store="tinydb",
                            immediate_sync=True,
                        )

                        logger.info(
                            f"Updated task {task_id} with result and status COMPLETED (with transaction)"
                        )
                except Exception as e:
                    logger.error(f"Failed to update task {task_id} with result: {e}")
                    # Still return the result even if storing failed
            else:
                # Update task with result and status in memory only
                task.result = result
                task.update_status(TaskStatus.COMPLETED)

            logger.info(f"Executed task {task_id} with result: {result}")
            return {"success": True, "result": result}

        except Exception as e:
            # Use a transaction if memory manager is available
            if self.memory_manager:
                try:
                    # Begin transaction
                    with self.memory_manager.begin_transaction(["tinydb", "graph"]):
                        # Update task status to FAILED and store error
                        task.result = {"error": str(e)}
                        task.update_status(TaskStatus.FAILED)

                        # Store updated task in memory
                        from .collaboration_memory_utils import store_with_retry

                        store_with_retry(
                            self.memory_manager,
                            task,
                            primary_store="tinydb",
                            immediate_sync=True,
                        )

                        logger.info(
                            f"Updated task {task_id} status to FAILED (with transaction)"
                        )
                except Exception as store_error:
                    logger.error(
                        f"Failed to update task {task_id} status to FAILED: {store_error}"
                    )
            else:
                # Update task status to FAILED and store error in memory only
                task.result = {"error": str(e)}
                task.update_status(TaskStatus.FAILED)

            logger.error(f"Error executing task {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def execute_workflow(self, tasks: list[CollaborationTask]) -> dict[str, Any]:
        """
        Execute a workflow consisting of multiple tasks.

        This method handles task dependencies and executes tasks in the correct order.
        It also supports parallel execution of independent tasks.

        Args:
            tasks: List of tasks in the workflow

        Returns:
            Results of all tasks in the workflow
        """
        # Register all tasks
        for task in tasks:
            self.tasks[task.id] = task

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(tasks)

        # Execute tasks in topological order
        results = {}
        executed_tasks = set()

        while len(executed_tasks) < len(tasks):
            # Find tasks that can be executed (all dependencies satisfied)
            executable_tasks = []

            for task in tasks:
                if task.id in executed_tasks:
                    continue

                dependencies = dependency_graph.get(task.id, set())
                if all(dep in executed_tasks for dep in dependencies):
                    executable_tasks.append(task)

            if not executable_tasks:
                logger.error("Circular dependency detected in workflow")
                return {"success": False, "error": "Circular dependency detected"}

            # Execute tasks in parallel (for now, just sequentially)
            for task in executable_tasks:
                # Assign the task to an agent
                self.assign_task(task.id)

                # Execute the task
                result = self.execute_task(task.id)
                results[task.id] = result
                executed_tasks.add(task.id)

        return {"success": True, "results": results}

    def _build_dependency_graph(
        self, tasks: list[CollaborationTask]
    ) -> dict[str, set[str]]:
        """
        Build a dependency graph for a list of tasks.

        Args:
            tasks: List of tasks

        Returns:
            Dictionary mapping task IDs to sets of dependency task IDs
        """
        dependency_graph = {}

        for task in tasks:
            dependency_graph[task.id] = set(task.dependencies)

        return dependency_graph

    def get_task(self, task_id: str) -> CollaborationTask | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_message(self, message_id: str) -> AgentMessage | None:
        """Get a message by ID."""
        return self.messages.get(message_id)

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def get_team(self, team_id: str) -> WSDETeam | None:
        """Get a team by ID."""
        return self.teams.get(team_id)
