"""Typed data transfer objects used by the requirements application layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections.abc import Mapping, Sequence
from uuid import UUID

from devsynth.domain.models.requirement import (
    ImpactAssessment,
    Requirement,
    RequirementChange,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


class EDRRPhase(str, Enum):
    """Enumerate the phases of the Explore-Define-Refine-Retrospect loop."""

    EXPAND = "EXPAND"
    REFINE = "REFINE"
    RETROSPECT = "RETROSPECT"


@dataclass(slots=True, frozen=True)
class RequirementUpdateDTO:
    """Structured payload describing a partial requirement update."""

    title: str | None = None
    description: str | None = None
    status: RequirementStatus | None = None
    priority: RequirementPriority | None = None
    type: RequirementType | None = None
    dependencies: Sequence[UUID] | None = None
    tags: Sequence[str] | None = None
    metadata: Mapping[str, str] | None = None

    def to_update_kwargs(self) -> dict[str, object]:
        """Render the DTO into keyword arguments for :meth:`Requirement.update`."""

        updates: dict[str, object] = {}
        if self.title is not None:
            updates["title"] = self.title
        if self.description is not None:
            updates["description"] = self.description
        if self.status is not None:
            updates["status"] = self.status
        if self.priority is not None:
            updates["priority"] = self.priority
        if self.type is not None:
            updates["type"] = self.type
        if self.dependencies is not None:
            updates["dependencies"] = list(self.dependencies)
        if self.tags is not None:
            updates["tags"] = list(self.tags)
        if self.metadata is not None:
            updates["metadata"] = dict(self.metadata)
        return updates


@dataclass(slots=True, frozen=True)
class ChangeAuditRecord:
    """Audit metadata captured whenever a requirement change is processed."""

    change: RequirementChange
    actor_id: str
    edrr_phase: EDRRPhase
    reason: str | None = None
    triggered_at: datetime = field(default_factory=datetime.now)

    @property
    def requirement(self) -> Requirement | None:
        """Return the requirement state associated with the change, if any."""

        return self.change.new_state or self.change.previous_state


class ChangeNotificationEvent(str, Enum):
    """Enumerate the lifecycle events for requirement change notifications."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(slots=True, frozen=True)
class ChangeNotificationPayload:
    """Structured payload passed to :class:`NotificationPort` implementations."""

    audit: ChangeAuditRecord
    event: ChangeNotificationEvent

    @property
    def change(self) -> RequirementChange:
        """Expose the underlying change for convenience."""

        return self.audit.change


@dataclass(slots=True, frozen=True)
class ImpactNotificationPayload:
    """Payload describing a completed impact assessment notification."""

    assessment: ImpactAssessment
    edrr_phase: EDRRPhase
    triggered_at: datetime = field(default_factory=datetime.now)


__all__ = [
    "ChangeAuditRecord",
    "ChangeNotificationEvent",
    "ChangeNotificationPayload",
    "EDRRPhase",
    "ImpactNotificationPayload",
    "RequirementUpdateDTO",
]
