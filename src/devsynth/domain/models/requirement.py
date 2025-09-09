"""
Domain models for requirements management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import UUID, uuid4


class RequirementStatus(Enum):
    """Status of a requirement."""

    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    DEPRECATED = "deprecated"


class RequirementPriority(Enum):
    """Priority of a requirement."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementType(Enum):
    """Type of a requirement."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"
    BUSINESS = "business"
    TECHNICAL = "technical"
    USER = "user"


@dataclass
class Requirement:
    """
    Domain model representing a requirement.
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str = ""
    status: RequirementStatus = RequirementStatus.DRAFT
    priority: RequirementPriority = RequirementPriority.MEDIUM
    type: RequirementType = RequirementType.FUNCTIONAL
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    dependencies: List[UUID] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def update(self, **kwargs) -> None:
        """
        Update requirement attributes.

        Args:
            **kwargs: Attributes to update.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()


class ChangeType(Enum):
    """Type of change to a requirement."""

    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"


@dataclass
class RequirementChange:
    """
    Domain model representing a change to a requirement.
    """

    id: UUID = field(default_factory=uuid4)
    requirement_id: Optional[UUID] = None
    change_type: ChangeType = ChangeType.MODIFY
    previous_state: Optional[Requirement] = None
    new_state: Optional[Requirement] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    reason: str = ""
    approved: bool = False
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    comments: List[str] = field(default_factory=list)


@dataclass
class ImpactAssessment:
    """
    Domain model representing an impact assessment for a requirement change.
    """

    id: UUID = field(default_factory=uuid4)
    change_id: UUID = None
    affected_requirements: List[UUID] = field(default_factory=list)
    affected_components: List[str] = field(default_factory=list)
    risk_level: str = "low"
    estimated_effort: str = "low"
    analysis: str = ""
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class DialecticalReasoning:
    """
    Domain model representing a dialectical reasoning session for a requirement change.
    """

    id: UUID = field(default_factory=uuid4)
    change_id: UUID = None
    thesis: str = ""
    antithesis: str = ""
    synthesis: str = ""
    arguments: List[Dict[str, str]] = field(default_factory=list)
    conclusion: str = ""
    recommendation: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class ChatMessage:
    """
    Domain model representing a chat message in a dialectical reasoning session.
    """

    id: UUID = field(default_factory=uuid4)
    session_id: UUID = None
    sender: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ChatSession:
    """
    Domain model representing a chat session for dialectical reasoning.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    reasoning_id: Optional[UUID] = None
    change_id: Optional[UUID] = None
    messages: List[ChatMessage] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, sender: str, content: str) -> ChatMessage:
        """
        Add a message to the chat session.

        Args:
            sender: The sender of the message.
            content: The content of the message.

        Returns:
            The created chat message.
        """
        message = ChatMessage(session_id=self.id, sender=sender, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
