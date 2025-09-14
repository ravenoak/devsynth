"""In-memory repository implementations for requirements management."""

from uuid import UUID

from devsynth.domain.models.requirement import (
    ChatMessage,
    ChatSession,
    DialecticalReasoning,
    ImpactAssessment,
    Requirement,
    RequirementChange,
)
from devsynth.ports.requirement_port import (
    ChangeRepositoryPort,
    ChatRepositoryPort,
    DialecticalReasoningRepositoryPort,
    ImpactAssessmentRepositoryPort,
    RequirementRepositoryPort,
)


class InMemoryRequirementRepository(RequirementRepositoryPort):
    """In-memory implementation of the requirement repository."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self.requirements: dict[UUID, Requirement] = {}

    def get_requirement(self, requirement_id: UUID) -> Requirement | None:
        """
        Get a requirement by ID.

        Args:
            requirement_id: The ID of the requirement.

        Returns:
            The requirement if found, None otherwise.
        """
        return self.requirements.get(requirement_id)

    def get_all_requirements(self) -> list[Requirement]:
        """Get all requirements."""
        return list(self.requirements.values())

    def save_requirement(self, requirement: Requirement) -> Requirement:
        """Save a requirement."""
        self.requirements[requirement.id] = requirement
        return requirement

    def delete_requirement(self, requirement_id: UUID) -> bool:
        """Delete a requirement."""
        if requirement_id in self.requirements:
            del self.requirements[requirement_id]
            return True
        return False

    def get_requirements_by_status(self, status: str) -> list[Requirement]:
        """Get requirements by status."""
        return [req for req in self.requirements.values() if req.status.value == status]

    def get_requirements_by_type(self, type_: str) -> list[Requirement]:
        """Get requirements by type."""
        return [req for req in self.requirements.values() if req.type.value == type_]


class InMemoryChangeRepository(ChangeRepositoryPort):
    """In-memory implementation of the change repository."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self.changes: dict[UUID, RequirementChange] = {}

    def get_change(self, change_id: UUID) -> RequirementChange | None:
        """
        Get a change by ID.

        Args:
            change_id: The ID of the change.

        Returns:
            The change if found, None otherwise.
        """
        return self.changes.get(change_id)

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
        return [
            change
            for change in self.changes.values()
            if change.requirement_id == requirement_id
        ]

    def save_change(self, change: RequirementChange) -> RequirementChange:
        """
        Save a change.

        Args:
            change: The change to save.

        Returns:
            The saved change.
        """
        self.changes[change.id] = change
        return change

    def delete_change(self, change_id: UUID) -> bool:
        """
        Delete a change.

        Args:
            change_id: The ID of the change to delete.

        Returns:
            True if the change was deleted, False otherwise.
        """
        if change_id in self.changes:
            del self.changes[change_id]
            return True
        return False


class InMemoryImpactAssessmentRepository(ImpactAssessmentRepositoryPort):
    """In-memory implementation of the impact assessment repository."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self.assessments: dict[UUID, ImpactAssessment] = {}
        self.change_to_assessment: dict[UUID, UUID] = {}

    def get_impact_assessment(self, assessment_id: UUID) -> ImpactAssessment | None:
        """
        Get an impact assessment by ID.

        Args:
            assessment_id: The ID of the impact assessment.

        Returns:
            The impact assessment if found, None otherwise.
        """
        return self.assessments.get(assessment_id)

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
        assessment_id = self.change_to_assessment.get(change_id)
        if assessment_id:
            return self.assessments.get(assessment_id)
        return None

    def save_impact_assessment(self, assessment: ImpactAssessment) -> ImpactAssessment:
        """Save an impact assessment."""
        self.assessments[assessment.id] = assessment
        if assessment.change_id:
            self.change_to_assessment[assessment.change_id] = assessment.id
        return assessment


class InMemoryDialecticalReasoningRepository(DialecticalReasoningRepositoryPort):
    """In-memory implementation of the dialectical reasoning repository."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self.reasonings: dict[UUID, DialecticalReasoning] = {}
        self.change_to_reasoning: dict[UUID, UUID] = {}

    def get_reasoning(self, reasoning_id: UUID) -> DialecticalReasoning | None:
        """
        Get a dialectical reasoning by ID.

        Args:
            reasoning_id: The ID of the dialectical reasoning.

        Returns:
            The dialectical reasoning if found, None otherwise.
        """
        return self.reasonings.get(reasoning_id)

    def get_reasoning_for_change(self, change_id: UUID) -> DialecticalReasoning | None:
        """
        Get a dialectical reasoning for a change.

        Args:
            change_id: The ID of the change.

        Returns:
            The dialectical reasoning if found, None otherwise.
        """
        reasoning_id = self.change_to_reasoning.get(change_id)
        if reasoning_id:
            return self.reasonings.get(reasoning_id)
        return None

    def save_reasoning(self, reasoning: DialecticalReasoning) -> DialecticalReasoning:
        """Save a dialectical reasoning."""
        self.reasonings[reasoning.id] = reasoning
        if reasoning.change_id:
            self.change_to_reasoning[reasoning.change_id] = reasoning.id
        return reasoning


class InMemoryChatRepository(ChatRepositoryPort):
    """In-memory implementation of the chat repository."""

    def __init__(self) -> None:
        """Initialize the repository."""
        self.sessions: dict[UUID, ChatSession] = {}
        self.messages: dict[UUID, ChatMessage] = {}
        self.user_sessions: dict[str, list[UUID]] = {}

    def get_session(self, session_id: UUID) -> ChatSession | None:
        """
        Get a chat session by ID.

        Args:
            session_id: The ID of the chat session.

        Returns:
            The chat session if found, None otherwise.
        """
        return self.sessions.get(session_id)

    def get_sessions_for_user(self, user_id: str) -> list[ChatSession]:
        """
        Get chat sessions for a user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of chat sessions for the user.
        """
        session_ids = self.user_sessions.get(user_id, [])
        return [
            self.sessions[session_id]
            for session_id in session_ids
            if session_id in self.sessions
        ]

    def save_session(self, session: ChatSession) -> ChatSession:
        """Save a chat session."""
        self.sessions[session.id] = session

        # Update user sessions mapping
        if session.user_id not in self.user_sessions:
            self.user_sessions[session.user_id] = []
        if session.id not in self.user_sessions[session.user_id]:
            self.user_sessions[session.user_id].append(session.id)

        return session

    def save_message(self, message: ChatMessage) -> ChatMessage:
        """Save a chat message."""
        self.messages[message.id] = message
        return message

    def get_messages_for_session(self, session_id: UUID) -> list[ChatMessage]:
        """Get messages for a chat session."""
        return [msg for msg in self.messages.values() if msg.session_id == session_id]
