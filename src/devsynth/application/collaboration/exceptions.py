# mypy: ignore-errors

"""Exceptions for the collaboration module."""

from typing import Any, Dict, Optional

from devsynth.exceptions import AgentExecutionError as BaseAgentExecutionError
from devsynth.exceptions import CollaborationError as BaseCollaborationError
from devsynth.exceptions import ConsensusError as BaseConsensusError
from devsynth.exceptions import DevSynthError
from devsynth.exceptions import RoleAssignmentError as BaseRoleAssignmentError
from devsynth.exceptions import TeamConfigurationError as BaseTeamConfigurationError
from devsynth.logging_setup import DevSynthLogger

from .dto import ConsensusOutcome, serialize_collaboration_dto

# Create a logger for this module
logger = DevSynthLogger(__name__)


# For backward compatibility, redefine the exceptions with the same interface
class CollaborationError(BaseCollaborationError):
    """Base exception for collaboration errors."""

    def __init__(self, message, agent_id=None, role=None, task=None, error_code=None):
        super().__init__(
            message, agent_id=agent_id, role=role, task=task, error_code=error_code
        )


class AgentExecutionError(BaseAgentExecutionError):
    """Exception raised when an agent fails to execute a task."""

    def __init__(self, message, agent_id=None, role=None, task=None, error_code=None):
        super().__init__(message, agent_id=agent_id, task=task, error_code=error_code)


class ConsensusError(BaseConsensusError):
    """Exception raised when agents cannot reach consensus."""

    def __init__(
        self,
        message,
        agent_id=None,
        role=None,
        task=None,
        agent_ids=None,
        topic=None,
        error_code=None,
    ):
        super().__init__(
            message,
            agent_ids=agent_ids or ([agent_id] if agent_id else None),
            topic=topic,
            error_code=error_code,
        )


class PeerReviewConsensusError(ConsensusError):
    """Exception raised when peer review consensus cannot be established."""

    def __init__(
        self,
        message: str,
        *,
        outcome: ConsensusOutcome | None = None,
        review_id: str | None = None,
        consensus_payload: dict[str, Any] | None = None,
        error_code: str | None = "PEER_REVIEW_CONSENSUS",
    ) -> None:
        super().__init__(
            message,
            agent_ids=None,
            topic="peer_review",
            error_code=error_code,
        )
        self.outcome = outcome
        self.review_id = review_id
        self.consensus_payload = consensus_payload

    def __str__(self) -> str:
        base = super().__str__()
        if self.review_id:
            return f"{base} [review_id={self.review_id}]"
        return base

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"message": str(self)}
        if self.review_id:
            data["review_id"] = self.review_id
        if self.outcome is not None:
            data["consensus"] = serialize_collaboration_dto(self.outcome)
        elif self.consensus_payload is not None:
            data["consensus"] = dict(self.consensus_payload)
        return data


class RoleAssignmentError(BaseRoleAssignmentError):
    """Exception raised when there's an issue with role assignment."""

    def __init__(self, message, agent_id=None, role=None, task=None, error_code=None):
        super().__init__(message, agent_id=agent_id, role=role, error_code=error_code)


class TeamConfigurationError(BaseTeamConfigurationError):
    """Exception raised when there's an issue with team configuration."""

    def __init__(
        self,
        message,
        agent_id=None,
        role=None,
        task=None,
        team_id=None,
        error_code=None,
    ):
        # BaseTeamConfigurationError expects message, team_id, and error_code
        # but it's trying to pass details to CollaborationError which doesn't accept it
        # We need to modify how we call the parent class

        # First, create a new instance of CollaborationError with the correct parameters
        collaboration_error = CollaborationError(
            message=message,
            agent_id=agent_id,
            role=role,
            task=task,
            error_code=error_code or "TEAM_CONFIGURATION_ERROR",
        )

        # Then copy its attributes to this instance
        self.message = collaboration_error.message
        self.error_code = collaboration_error.error_code
        self.details = collaboration_error.details.copy()

        # Add team_id to details if provided
        if team_id is not None:
            self.details["team_id"] = team_id

        # Initialize the Exception base class
        Exception.__init__(self, message)
