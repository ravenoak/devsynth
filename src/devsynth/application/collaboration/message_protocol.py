from __future__ import annotations

"""Message passing protocol for WSDE agents."""

import json
import os
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Type, Union
from uuid import uuid4


class MessageType(Enum):
    """Supported message types."""

    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    INFORMATION_REQUEST = "information_request"
    REVIEW_REQUEST = "review_request"
    DECISION_REQUEST = "decision_request"
    NOTIFICATION = "notification"


@dataclass
class Message:
    """A structured message exchanged between agents."""

    message_id: str
    message_type: MessageType
    sender: str
    recipients: List[str]
    subject: str
    content: MessagePayload
    metadata: Optional[MemorySyncPort]
    timestamp: datetime

    def to_ordered_dict(self) -> Dict[str, JSONValue]:
        data: "OrderedDict[str, JSONValue]" = OrderedDict()
        data["message_id"] = self.message_id
        data["message_type"] = self.message_type.value
        data["sender"] = self.sender
        data["recipients"] = list(self.recipients)
        data["subject"] = self.subject
        data["content"] = serialize_message_payload(self.content)
        data["metadata"] = serialize_memory_sync_port(self.metadata)
        data["timestamp"] = self.timestamp.isoformat()
        return dict(data)


@dataclass
class MessageThread:
    """Group of messages in a conversation."""

    thread_id: str
    participants: List[str]
    messages: List[str] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        if message.message_id not in self.messages:
            self.messages.append(message.message_id)


class MessageStore:
    """Simple JSON file-based storage for messages."""

    def __init__(self, storage_file: Optional[str] = None) -> None:
        self.storage_file = storage_file or os.path.join(
            os.getcwd(), ".devsynth", "messages.json"
        )
        self._ensure_directory_exists()
        self.messages: Dict[str, Message] = self._load_messages()

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _ensure_directory_exists(self) -> None:
        directory = os.path.dirname(self.storage_file)
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if not no_file_logging:
            os.makedirs(directory, exist_ok=True)

    def _load_messages(self) -> Dict[str, Message]:
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if no_file_logging or not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {}

        messages = {}
        for item in data.get("messages", []):
            try:
                content = deserialize_message_payload(item.get("content"))
                metadata_raw = item.get("metadata")
                metadata_obj: Optional[MemorySyncPort]
                try:
                    metadata_obj = ensure_memory_sync_port(metadata_raw)
                except Exception:
                    metadata_obj = None
                msg = Message(
                    message_id=item["message_id"],
                    message_type=MessageType(item["message_type"]),
                    sender=item["sender"],
                    recipients=item.get("recipients", []),
                    subject=item.get("subject", ""),
                    content=content,
                    metadata=metadata_obj,
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                )
                messages[msg.message_id] = msg
            except Exception:
                continue
        return messages

    def _save_messages(self) -> None:
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if no_file_logging:
            return
        data = {"messages": [m.to_ordered_dict() for m in self.messages.values()]}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_message(self, message: Message) -> None:
        self.messages[message.message_id] = message
        self._save_messages()

    def get_all_messages(self) -> List[Message]:
        return self.get_messages()

    def get_messages(self, filters: Optional[MessageFilter] = None) -> List[Message]:
        messages = list(self.messages.values())
        if filters is None:
            return messages
        return [m for m in messages if self._matches_filter(m, filters)]

    @staticmethod
    def _coerce_message_type(value: str) -> MessageType:
        try:
            return MessageType(value)
        except ValueError:
            try:
                return MessageType[value]
            except KeyError as exc:  # pragma: no cover - defensive
                raise ValueError(f"Unknown message type: {value!r}") from exc

    def _matches_filter(self, message: Message, filters: MessageFilter) -> bool:
        if filters.message_type:
            expected_type = self._coerce_message_type(filters.message_type)
            if message.message_type != expected_type:
                return False
        if filters.sender and message.sender != filters.sender:
            return False
        if filters.recipient and filters.recipient not in message.recipients:
            return False
        if (
            filters.subject_contains
            and filters.subject_contains.lower() not in message.subject.lower()
        ):
            return False
        if filters.since is not None and message.timestamp < filters.since:
            return False
        if filters.until is not None and message.timestamp > filters.until:
            return False
        return True


from ...domain.models.memory import MemoryItem, MemoryType
from ..memory.memory_manager import MemoryManager
from .dto import (
    AgentPayload,
    CollaborationDTO,
    CollaborationPayloadInput,
    ConsensusOutcome,
    JSONValue,
    MemorySyncPort,
    MessageFilter,
    MessageFilterInput,
    MessagePayload,
    PeerReviewRecord,
    TaskDescriptor,
    deserialize_message_payload,
    ensure_collaboration_payload,
    ensure_memory_sync_port,
    ensure_message_filter,
    serialize_memory_sync_port,
    serialize_message_payload,
)

MESSAGE_TYPE_DEFAULTS: Dict[MessageType, Type[CollaborationDTO]] = {
    MessageType.TASK_ASSIGNMENT: TaskDescriptor,
    MessageType.REVIEW_REQUEST: PeerReviewRecord,
    MessageType.DECISION_REQUEST: ConsensusOutcome,
    MessageType.STATUS_UPDATE: AgentPayload,
    MessageType.INFORMATION_REQUEST: AgentPayload,
    MessageType.NOTIFICATION: AgentPayload,
}


class MessageProtocol:
    """Message passing implementation with optional persistence."""

    def __init__(
        self,
        store: Optional[MessageStore] = None,
        memory_manager: Optional[MemoryManager] = None,
    ) -> None:
        self.store = store or MessageStore()
        self.history: List[Message] = self.store.get_messages()
        self.memory_manager = memory_manager

    def send_message(
        self,
        sender: str,
        recipients: List[str],
        message_type: Union[MessageType, str],
        subject: str,
        content: CollaborationPayloadInput,
        metadata: Optional[Union[MemorySyncPort, Mapping[str, JSONValue]]] = None,
    ) -> Message:
        """Create and store a message."""

        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        default_payload_type: Type[CollaborationDTO]
        default_payload_type = MESSAGE_TYPE_DEFAULTS.get(message_type, AgentPayload)
        payload = ensure_collaboration_payload(content, default=default_payload_type)
        metadata_obj = ensure_memory_sync_port(metadata)
        message = Message(
            message_id=str(uuid4()),
            message_type=message_type,
            sender=sender,
            recipients=recipients,
            subject=subject,
            content=payload,
            metadata=metadata_obj,
            timestamp=datetime.now(),
        )
        # High priority messages are inserted at the front of the history
        priority = None
        if message.metadata is not None:
            priority = message.metadata.priority or message.metadata.options.get(
                "priority"
            )
        if priority == "high":
            self.history.insert(0, message)
        else:
            self.history.append(message)

        self.store.add_message(message)

        if self.memory_manager is not None:
            serialized_message = message.to_ordered_dict()
            item = MemoryItem(
                id=message.message_id,
                content=serialized_message,
                memory_type=MemoryType.CONVERSATION,
                metadata=serialize_memory_sync_port(message.metadata) or {},
            )
            try:
                if "tinydb" in self.memory_manager.adapters:
                    primary = "tinydb"
                elif "graph" in self.memory_manager.adapters:
                    primary = "graph"
                elif self.memory_manager.adapters:
                    primary = next(iter(self.memory_manager.adapters))
                else:
                    primary = None

                if primary:
                    self.memory_manager.update_item(primary, item)
                    try:
                        self.memory_manager.flush_updates()
                    except Exception:
                        pass
            except Exception:
                pass
        return message

    def get_messages(
        self,
        agent: Optional[str] = None,
        filters: Optional[MessageFilterInput] = None,
    ) -> List[Message]:
        """Retrieve messages optionally filtered by agent or criteria."""

        filter_obj = ensure_message_filter(filters) if filters is not None else None
        messages = self.store.get_messages(filter_obj)
        if agent:
            messages = [
                m for m in messages if agent in m.recipients or m.sender == agent
            ]
        return messages
