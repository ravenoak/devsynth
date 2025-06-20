from __future__ import annotations

"""Message passing protocol for WSDE agents."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
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
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime


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
        self.messages: Dict[str, Message] = {}
        self.history: List[str] = []
        self.messages, self.history = self._load_messages()

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

    def _load_messages(self) -> tuple[Dict[str, Message], List[str]]:
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if no_file_logging or not os.path.exists(self.storage_file):
            return {}, []
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {}, []

        messages: Dict[str, Message] = {}
        for item in data.get("messages", []):
            try:
                msg = Message(
                    message_id=item["message_id"],
                    message_type=MessageType(item["message_type"]),
                    sender=item["sender"],
                    recipients=item.get("recipients", []),
                    subject=item.get("subject", ""),
                    content=item.get("content"),
                    metadata=item.get("metadata", {}),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                )
                messages[msg.message_id] = msg
            except Exception:
                continue
        history = data.get(
            "history", [m["message_id"] for m in data.get("messages", [])]
        )
        return messages, history

    def _save_messages(self) -> None:
        no_file_logging = os.environ.get("DEVSYNTH_NO_FILE_LOGGING", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if no_file_logging:
            return
        data = {
            "messages": [
                {
                    "message_id": m.message_id,
                    "message_type": m.message_type.value,
                    "sender": m.sender,
                    "recipients": m.recipients,
                    "subject": m.subject,
                    "content": m.content,
                    "metadata": m.metadata,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in self.get_all_messages()
            ],
            "history": self.history,
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_message(self, message: Message, position: Optional[int] = None) -> None:
        self.messages[message.message_id] = message
        if position is None:
            self.history.append(message.message_id)
        else:
            self.history.insert(position, message.message_id)
        self._save_messages()

    def get_all_messages(self) -> List[Message]:
        return [self.messages[mid] for mid in self.history if mid in self.messages]


class MessageProtocol:
    """Message passing implementation with optional persistence."""

    def __init__(self, store: Optional[MessageStore] = None) -> None:
        self.store = store or MessageStore()
        self.history: List[Message] = self.store.get_all_messages()

    def send_message(
        self,
        sender: str,
        recipients: List[str],
        message_type: MessageType | str,
        subject: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Create and store a message."""

        if isinstance(message_type, str):
            message_type = MessageType(message_type)
        message = Message(
            message_id=str(uuid4()),
            message_type=message_type,
            sender=sender,
            recipients=recipients,
            subject=subject,
            content=content,
            metadata=metadata or {},
            timestamp=datetime.now(),
        )
        priority = message.metadata.get("priority", "normal")
        if priority == "high":
            index = 0
        elif priority == "normal":
            high_count = len(
                [m for m in self.history if m.metadata.get("priority") == "high"]
            )
            index = high_count
        else:
            index = len(self.history)

        self.history.insert(index, message)
        self.store.add_message(message, position=index)
        return message

    def get_messages(
        self, agent: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Message]:
        """Retrieve messages optionally filtered by agent or criteria."""

        messages = list(self.store.get_all_messages())
        if agent:
            messages = [
                m for m in messages if agent in m.recipients or m.sender == agent
            ]
        if filters:
            if "message_type" in filters:
                mt = filters["message_type"]
                mt = MessageType(mt) if isinstance(mt, str) else mt
                messages = [m for m in messages if m.message_type == mt]
            if "since" in filters:
                messages = [m for m in messages if m.timestamp >= filters["since"]]
        return messages
