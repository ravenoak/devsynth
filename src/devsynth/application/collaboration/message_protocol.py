from __future__ import annotations

"""Message passing protocol for WSDE agents."""

from dataclasses import dataclass
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


class MessageProtocol:
    """Simple in-memory message passing implementation."""

    def __init__(self) -> None:
        self.history: List[Message] = []

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
        # High priority messages are inserted at the front of the history
        if message.metadata.get("priority") == "high":
            self.history.insert(0, message)
        else:
            self.history.append(message)
        return message

    def get_messages(
        self, agent: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Message]:
        """Retrieve messages optionally filtered by agent or criteria."""

        messages = list(self.history)
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
