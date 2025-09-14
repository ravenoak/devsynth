"""
Domain models for requirements management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
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
    """Represent a requirement with immutable identity and tracked metadata.

    Guarantees:
        * ``id`` uniquely identifies the requirement within the system.
        * ``dependencies`` only contains UUIDs referencing other requirements.
        * ``updated_at`` is refreshed on any call to :meth:`update`.
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
    dependencies: list[UUID] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def update(self, **kwargs: Any) -> None:
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
    """Capture a single change applied to a :class:`Requirement`.

    Guarantees:
        * ``id`` uniquely identifies the change event.
        * ``previous_state`` and ``new_state`` hold snapshots of the
          requirement before and after modification.
    """

    id: UUID = field(default_factory=uuid4)
    requirement_id: UUID | None = None
    change_type: ChangeType = ChangeType.MODIFY
    previous_state: Requirement | None = None
    new_state: Requirement | None = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    reason: str = ""
    approved: bool = False
    approved_at: datetime | None = None
    approved_by: str | None = None
    comments: list[str] = field(default_factory=list)


@dataclass
class ImpactAssessment:
    """Summarize the projected impact of a change.

    Guarantees:
        * ``affected_requirements`` and ``affected_components`` are populated
          with identifiers rather than nested objects.
        * ``created_at`` records when the assessment was produced.
    """

    id: UUID = field(default_factory=uuid4)
    change_id: UUID | None = None
    affected_requirements: list[UUID] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    risk_level: str = "low"
    estimated_effort: str = "low"
    analysis: str = ""
    recommendations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class DialecticalReasoning:
    """Record the reasoning process around a proposed change.

    Guarantees:
        * ``arguments`` preserves the sequence of thesis/antithesis exchanges.
        * ``updated_at`` advances whenever new arguments are appended.
    """

    id: UUID = field(default_factory=uuid4)
    change_id: UUID | None = None
    thesis: str = ""
    antithesis: str = ""
    synthesis: str = ""
    arguments: list[dict[str, str]] = field(default_factory=list)
    conclusion: str = ""
    recommendation: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""


@dataclass
class ChatMessage:
    """A single message within a :class:`ChatSession`.

    Guarantees:
        * ``timestamp`` is set when the message is created.
        * ``metadata`` stores arbitrary string key/value pairs.
    """

    id: UUID = field(default_factory=uuid4)
    session_id: UUID | None = None
    sender: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ChatSession:
    """Manage chat messages tied to a reasoning session.

    Guarantees:
        * ``messages`` contains only :class:`ChatMessage` instances.
        * ``updated_at`` reflects the timestamp of the most recent message.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    reasoning_id: UUID | None = None
    change_id: UUID | None = None
    messages: list[ChatMessage] = field(default_factory=list)
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
