"""Ports defining boundary contracts for requirement operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from uuid import UUID

from devsynth.application.requirements.models import (
    ChangeNotificationPayload,
    EDRRPhase,
    ImpactNotificationPayload,
)
from devsynth.domain.models.requirement import (
    ChatMessage,
    ChatSession,
    DialecticalReasoning,
    ImpactAssessment,
    Requirement,
    RequirementChange,
)


class RequirementRepositoryPort(ABC):
    """Port for requirement repository."""

    @abstractmethod
    def get_requirement(self, requirement_id: UUID) -> Requirement | None:
        """
        Get a requirement by ID.

        Args:
            requirement_id: The ID of the requirement.

        Returns:
            The requirement if found, None otherwise.
        """
        return None

    @abstractmethod
    def get_all_requirements(self) -> list[Requirement]:
        """
        Get all requirements.

        Returns:
            A list of all requirements.
        """
        return []

    @abstractmethod
    def save_requirement(self, requirement: Requirement) -> Requirement:
        """
        Save a requirement.

        Args:
            requirement: The requirement to save.

        Returns:
            The saved requirement.
        """
        return requirement

    @abstractmethod
    def delete_requirement(self, requirement_id: UUID) -> bool:
        """
        Delete a requirement.

        Args:
            requirement_id: The ID of the requirement to delete.

        Returns:
            True if the requirement was deleted, False otherwise.
        """
        return False

    @abstractmethod
    def get_requirements_by_status(self, status: str) -> list[Requirement]:
        """
        Get requirements by status.

        Args:
            status: The status to filter by.

        Returns:
            A list of requirements with the specified status.
        """
        return []

    @abstractmethod
    def get_requirements_by_type(self, type_: str) -> list[Requirement]:
        """
        Get requirements by type.

        Args:
            type_: The type to filter by.

        Returns:
            A list of requirements with the specified type.
        """
        return []


class ChangeRepositoryPort(ABC):
    """Port for requirement change repository."""

    @abstractmethod
    def get_change(self, change_id: UUID) -> RequirementChange | None:
        """
        Get a change by ID.

        Args:
            change_id: The ID of the change.

        Returns:
            The change if found, None otherwise.
        """
        return None

    @abstractmethod
    def get_changes_for_requirement(
        self, requirement_id: UUID
    ) -> list[RequirementChange]:
        """
        Get changes for a requirement.

        Args:
            requirement_id: The ID of the requirement.

        Returns:
            A list of changes for the requirement.
        """
        return []

    @abstractmethod
    def save_change(self, change: RequirementChange) -> RequirementChange:
        """
        Save a change.

        Args:
            change: The change to save.

        Returns:
            The saved change.
        """
        return change

    @abstractmethod
    def delete_change(self, change_id: UUID) -> bool:
        """
        Delete a change.

        Args:
            change_id: The ID of the change to delete.

        Returns:
            True if the change was deleted, False otherwise.
        """
        return False


class ImpactAssessmentRepositoryPort(ABC):
    """Port for impact assessment repository."""

    @abstractmethod
    def get_impact_assessment(self, assessment_id: UUID) -> ImpactAssessment | None:
        """
        Get an impact assessment by ID.

        Args:
            assessment_id: The ID of the impact assessment.

        Returns:
            The impact assessment if found, None otherwise.
        """
        return None

    @abstractmethod
    def get_impact_assessment_for_change(
        self, change_id: UUID
    ) -> ImpactAssessment | None:
        """
        Get an impact assessment for a change.

        Args:
            change_id: The ID of the change.

        Returns:
            The impact assessment if found, None otherwise.
        """
        return None

    @abstractmethod
    def save_impact_assessment(self, assessment: ImpactAssessment) -> ImpactAssessment:
        """
        Save an impact assessment.

        Args:
            assessment: The impact assessment to save.

        Returns:
            The saved impact assessment.
        """
        return assessment


class DialecticalReasoningRepositoryPort(ABC):
    """Port for dialectical reasoning repository."""

    @abstractmethod
    def get_reasoning(self, reasoning_id: UUID) -> DialecticalReasoning | None:
        """
        Get a dialectical reasoning by ID.

        Args:
            reasoning_id: The ID of the dialectical reasoning.

        Returns:
            The dialectical reasoning if found, None otherwise.
        """
        return None

    @abstractmethod
    def get_reasoning_for_change(
        self, change_id: UUID
    ) -> DialecticalReasoning | None:
        """
        Get a dialectical reasoning for a change.

        Args:
            change_id: The ID of the change.

        Returns:
            The dialectical reasoning if found, None otherwise.
        """
        return None

    @abstractmethod
    def save_reasoning(self, reasoning: DialecticalReasoning) -> DialecticalReasoning:
        """
        Save a dialectical reasoning.

        Args:
            reasoning: The dialectical reasoning to save.

        Returns:
            The saved dialectical reasoning.
        """
        return reasoning


class ChatRepositoryPort(ABC):
    """Port for chat repository."""

    @abstractmethod
    def get_session(self, session_id: UUID) -> ChatSession | None:
        """
        Get a chat session by ID.

        Args:
            session_id: The ID of the chat session.

        Returns:
            The chat session if found, None otherwise.
        """
        return None

    @abstractmethod
    def get_sessions_for_user(self, user_id: str) -> list[ChatSession]:
        """
        Get chat sessions for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of chat sessions for the user.
        """
        return []

    @abstractmethod
    def save_session(self, session: ChatSession) -> ChatSession:
        """
        Save a chat session.

        Args:
            session: The chat session to save.

        Returns:
            The saved chat session.
        """
        return session

    @abstractmethod
    def save_message(self, message: ChatMessage) -> ChatMessage:
        """
        Save a chat message.

        Args:
            message: The chat message to save.

        Returns:
            The saved chat message.
        """
        return message

    @abstractmethod
    def get_messages_for_session(self, session_id: UUID) -> list[ChatMessage]:
        """
        Get messages for a chat session.

        Args:
            session_id: The ID of the chat session.

        Returns:
            A list of messages for the chat session.
        """
        return []


class DialecticalReasonerPort(ABC):
    """Port for dialectical reasoner."""

    @abstractmethod
    def evaluate_change(
        self,
        change: RequirementChange,
        edrr_phase: EDRRPhase = EDRRPhase.REFINE,
    ) -> DialecticalReasoning:
        """
        Evaluate a requirement change using dialectical reasoning.

        Args:
            change: The requirement change to evaluate.
            edrr_phase: The EDRR phase context for memory storage.

        Returns:
            The dialectical reasoning result.
        """
        return DialecticalReasoning(change_id=change.id)

    @abstractmethod
    def process_message(
        self, session_id: UUID, message: str, user_id: str
    ) -> ChatMessage:
        """
        Process a message in a dialectical reasoning chat session.

        Args:
            session_id: The ID of the chat session.
            message: The message content.
            user_id: The ID of the user sending the message.

        Returns:
            The response message.
        """
        return ChatMessage(session_id=session_id, sender="system", content="")

    @abstractmethod
    def create_session(
        self, user_id: str, change_id: UUID | None = None
    ) -> ChatSession:
        """
        Create a new dialectical reasoning chat session.

        Args:
            user_id: The ID of the user.
            change_id: The ID of the change to discuss, if any.

        Returns:
            The created chat session.
        """
        return ChatSession(user_id=user_id, change_id=change_id)

    @abstractmethod
    def assess_impact(
        self,
        change: RequirementChange,
        edrr_phase: EDRRPhase = EDRRPhase.REFINE,
    ) -> ImpactAssessment:
        """
        Assess the impact of a requirement change.

        Args:
            change: The requirement change to assess.
            edrr_phase: The EDRR phase context for memory storage.

        Returns:
            The impact assessment.
        """
        return ImpactAssessment(change_id=change.id)


class NotificationPort(ABC):
    """Port for notifications."""

    @abstractmethod
    def notify_change_proposed(self, payload: ChangeNotificationPayload) -> None:
        """
        Notify that a change has been proposed.

        Args:
            payload: Structured payload describing the proposed change.
        """
        return None

    @abstractmethod
    def notify_change_approved(self, payload: ChangeNotificationPayload) -> None:
        """
        Notify that a change has been approved.

        Args:
            payload: Structured payload describing the approved change.
        """
        return None

    @abstractmethod
    def notify_change_rejected(self, payload: ChangeNotificationPayload) -> None:
        """
        Notify that a change has been rejected.

        Args:
            payload: Structured payload describing the rejected change.
        """
        return None

    @abstractmethod
    def notify_impact_assessment_completed(
        self, payload: ImpactNotificationPayload
    ) -> None:
        """
        Notify that an impact assessment has been completed.

        Args:
            payload: Structured payload describing the completed impact assessment.
        """
        return None


class ChatPort(ABC):
    """Port for chat interface."""

    @abstractmethod
    def send_message(self, session_id: UUID, message: str, user_id: str) -> ChatMessage:
        """
        Send a message in a chat session.

        Args:
            session_id: The ID of the chat session.
            message: The message content.
            user_id: The ID of the user sending the message.

        Returns:
            The response message.
        """
        return ChatMessage(session_id=session_id, sender="system", content="")

    @abstractmethod
    def create_session(
        self, user_id: str, change_id: UUID | None = None
    ) -> ChatSession:
        """
        Create a new chat session.

        Args:
            user_id: The ID of the user.
            change_id: The ID of the change to discuss, if any.

        Returns:
            The created chat session.
        """
        return ChatSession(user_id=user_id, change_id=change_id)

    @abstractmethod
    def get_session(self, session_id: UUID) -> ChatSession | None:
        """
        Get a chat session by ID.

        Args:
            session_id: The ID of the chat session.

        Returns:
            The chat session if found, None otherwise.
        """
        return None

    @abstractmethod
    def get_sessions_for_user(self, user_id: str) -> list[ChatSession]:
        """
        Get chat sessions for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of chat sessions for the user.
        """
        return []

    @abstractmethod
    def get_messages_for_session(self, session_id: UUID) -> list[ChatMessage]:
        """
        Get messages for a chat session.

        Args:
            session_id: The ID of the chat session.

        Returns:
            A list of messages for the chat session.
        """
        return []
