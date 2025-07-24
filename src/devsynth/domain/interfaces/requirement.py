"""
Domain interfaces for requirements management.
"""

from typing import Dict, List, Optional
from uuid import UUID

from devsynth.domain.models.requirement import (
    ChatMessage,
    ChatSession,
    DialecticalReasoning,
    ImpactAssessment,
    Requirement,
    RequirementChange,
)


class RequirementRepositoryInterface:
    """Simple in-memory requirement repository."""

    def __init__(self) -> None:
        self.requirements: Dict[UUID, Requirement] = {}

    def get_requirement(self, requirement_id: UUID) -> Optional[Requirement]:
        return self.requirements.get(requirement_id)

    def get_all_requirements(self) -> List[Requirement]:
        return list(self.requirements.values())

    def save_requirement(self, requirement: Requirement) -> Requirement:
        self.requirements[requirement.id] = requirement
        return requirement

    def delete_requirement(self, requirement_id: UUID) -> bool:
        if requirement_id in self.requirements:
            del self.requirements[requirement_id]
            return True
        return False

    def get_requirements_by_status(self, status: str) -> List[Requirement]:
        return [r for r in self.requirements.values() if r.status.value == status]

    def get_requirements_by_type(self, type_: str) -> List[Requirement]:
        return [r for r in self.requirements.values() if r.type.value == type_]


class ChangeRepositoryInterface:
    """Simple in-memory repository for requirement changes."""

    def __init__(self) -> None:
        self.changes: Dict[UUID, RequirementChange] = {}

    def get_change(self, change_id: UUID) -> Optional[RequirementChange]:
        return self.changes.get(change_id)

    def get_changes_for_requirement(
        self, requirement_id: UUID
    ) -> List[RequirementChange]:
        return [c for c in self.changes.values() if c.requirement_id == requirement_id]

    def save_change(self, change: RequirementChange) -> RequirementChange:
        self.changes[change.id] = change
        return change

    def delete_change(self, change_id: UUID) -> bool:
        if change_id in self.changes:
            del self.changes[change_id]
            return True
        return False


class ImpactAssessmentRepositoryInterface:
    """Simple in-memory impact assessment repository."""

    def __init__(self) -> None:
        self.assessments: Dict[UUID, ImpactAssessment] = {}
        self.change_to_assessment: Dict[UUID, UUID] = {}

    def get_impact_assessment(self, assessment_id: UUID) -> Optional[ImpactAssessment]:
        return self.assessments.get(assessment_id)

    def get_impact_assessment_for_change(
        self, change_id: UUID
    ) -> Optional[ImpactAssessment]:
        assessment_id = self.change_to_assessment.get(change_id)
        if assessment_id:
            return self.assessments.get(assessment_id)
        return None

    def save_impact_assessment(self, assessment: ImpactAssessment) -> ImpactAssessment:
        self.assessments[assessment.id] = assessment
        if assessment.change_id:
            self.change_to_assessment[assessment.change_id] = assessment.id
        return assessment


class DialecticalReasoningRepositoryInterface:
    """Simple in-memory dialectical reasoning repository."""

    def __init__(self) -> None:
        self.reasonings: Dict[UUID, DialecticalReasoning] = {}
        self.change_to_reasoning: Dict[UUID, UUID] = {}

    def get_reasoning(self, reasoning_id: UUID) -> Optional[DialecticalReasoning]:
        return self.reasonings.get(reasoning_id)

    def get_reasoning_for_change(
        self, change_id: UUID
    ) -> Optional[DialecticalReasoning]:
        reasoning_id = self.change_to_reasoning.get(change_id)
        if reasoning_id:
            return self.reasonings.get(reasoning_id)
        return None

    def save_reasoning(self, reasoning: DialecticalReasoning) -> DialecticalReasoning:
        self.reasonings[reasoning.id] = reasoning
        if reasoning.change_id:
            self.change_to_reasoning[reasoning.change_id] = reasoning.id
        return reasoning


class ChatRepositoryInterface:
    """Simple in-memory chat repository."""

    def __init__(self) -> None:
        self.sessions: Dict[UUID, ChatSession] = {}
        self.messages: Dict[UUID, ChatMessage] = {}
        self.user_sessions: Dict[str, List[UUID]] = {}

    def get_session(self, session_id: UUID) -> Optional[ChatSession]:
        return self.sessions.get(session_id)

    def get_sessions_for_user(self, user_id: str) -> List[ChatSession]:
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def save_session(self, session: ChatSession) -> ChatSession:
        self.sessions[session.id] = session
        self.user_sessions.setdefault(session.user_id, [])
        if session.id not in self.user_sessions[session.user_id]:
            self.user_sessions[session.user_id].append(session.id)
        return session

    def save_message(self, message: ChatMessage) -> ChatMessage:
        self.messages[message.id] = message
        return message

    def get_messages_for_session(self, session_id: UUID) -> List[ChatMessage]:
        return [m for m in self.messages.values() if m.session_id == session_id]


class DialecticalReasonerInterface:
    """Base dialectical reasoner implementation."""

    def evaluate_change(self, change: RequirementChange) -> DialecticalReasoning:
        reasoning = DialecticalReasoning(change_id=change.id)
        reasoning.thesis = f"Proposed change {change.id}"
        reasoning.antithesis = "Opposing view"
        reasoning.synthesis = "Synthesis"
        reasoning.conclusion = "Unreviewed"
        reasoning.recommendation = "Review"
        return reasoning

    def process_message(
        self, session_id: UUID, message: str, user_id: str
    ) -> ChatMessage:
        return ChatMessage(session_id=session_id, sender="system", content=message)

    def create_session(
        self, user_id: str, change_id: Optional[UUID] = None
    ) -> ChatSession:
        return ChatSession(user_id=user_id, change_id=change_id)

    def assess_impact(self, change: RequirementChange) -> ImpactAssessment:
        return ImpactAssessment(change_id=change.id, analysis="")


class NotificationInterface:
    """Base notification service."""

    def notify_change_proposed(self, change: RequirementChange) -> None:
        print(f"Change proposed: {change.id}")

    def notify_change_approved(self, change: RequirementChange) -> None:
        print(f"Change approved: {change.id}")

    def notify_change_rejected(self, change: RequirementChange) -> None:
        print(f"Change rejected: {change.id}")

    def notify_impact_assessment_completed(self, assessment: ImpactAssessment) -> None:
        print(f"Impact assessment completed: {assessment.id}")


class InMemoryRequirementRepository(RequirementRepositoryInterface):
    """In-memory implementation of :class:`RequirementRepositoryInterface`."""

    def __init__(self) -> None:
        super().__init__()


class InMemoryChangeRepository(ChangeRepositoryInterface):
    """In-memory implementation of :class:`ChangeRepositoryInterface`."""

    def __init__(self) -> None:
        super().__init__()


class InMemoryImpactAssessmentRepository(ImpactAssessmentRepositoryInterface):
    """In-memory implementation of :class:`ImpactAssessmentRepositoryInterface`."""

    def __init__(self) -> None:
        super().__init__()


class InMemoryDialecticalReasoningRepository(DialecticalReasoningRepositoryInterface):
    """In-memory implementation of :class:`DialecticalReasoningRepositoryInterface`."""

    def __init__(self) -> None:
        super().__init__()


class InMemoryChatRepository(ChatRepositoryInterface):
    """In-memory implementation of :class:`ChatRepositoryInterface`."""

    def __init__(self) -> None:
        super().__init__()


class SimpleDialecticalReasoner(DialecticalReasonerInterface):
    """Minimal implementation of :class:`DialecticalReasonerInterface`."""

    def __init__(self, chat_repo: ChatRepositoryInterface) -> None:
        self.chat_repo = chat_repo

    def evaluate_change(self, change: RequirementChange) -> DialecticalReasoning:
        reasoning = DialecticalReasoning(change_id=change.id)
        reasoning.thesis = f"Proposed change {change.id}"
        reasoning.antithesis = "Opposing view"
        reasoning.synthesis = "Synthesis"
        reasoning.conclusion = "Unreviewed"
        reasoning.recommendation = "Review"
        return reasoning

    def process_message(
        self, session_id: UUID, message: str, user_id: str
    ) -> ChatMessage:
        session = self.chat_repo.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        user_msg = ChatMessage(session_id=session_id, sender=user_id, content=message)
        self.chat_repo.save_message(user_msg)
        response = ChatMessage(session_id=session_id, sender="system", content=message)
        self.chat_repo.save_message(response)
        return response

    def create_session(
        self, user_id: str, change_id: Optional[UUID] = None
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, change_id=change_id)
        self.chat_repo.save_session(session)
        return session

    def assess_impact(self, change: RequirementChange) -> ImpactAssessment:
        assessment = ImpactAssessment(change_id=change.id, analysis="None")
        return assessment


class PrintNotificationService(NotificationInterface):
    """Simple notification service that prints messages to stdout."""

    def notify_change_proposed(self, change: RequirementChange) -> None:
        print(f"Change proposed: {change.id}")

    def notify_change_approved(self, change: RequirementChange) -> None:
        print(f"Change approved: {change.id}")

    def notify_change_rejected(self, change: RequirementChange) -> None:
        print(f"Change rejected: {change.id}")

    def notify_impact_assessment_completed(self, assessment: ImpactAssessment) -> None:
        print(f"Impact assessment completed: {assessment.id}")
