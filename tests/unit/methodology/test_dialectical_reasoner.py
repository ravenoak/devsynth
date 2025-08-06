import pytest
from uuid import uuid4

from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.domain.interfaces.requirement import (
    RequirementRepositoryInterface,
    DialecticalReasoningRepositoryInterface,
    ImpactAssessmentRepositoryInterface,
    ChatRepositoryInterface,
)
from devsynth.domain.models.requirement import RequirementChange
from devsynth.domain.models.memory import MemoryType


class DummyNotification:
    def notify_change_proposed(self, change):
        pass

    def notify_change_approved(self, change):
        pass

    def notify_change_rejected(self, change):
        pass

    def notify_impact_assessment_completed(self, assessment):
        pass


class DummyLLM:
    def query(self, prompt: str) -> str:
        return "text"


class DummyMemoryManager:
    def __init__(self):
        self.calls = []

    def store_with_edrr_phase(self, content, memory_type, edrr_phase, metadata=None):
        self.calls.append((content, memory_type, edrr_phase, metadata))
        return "mem-1"


@pytest.mark.medium
def test_evaluate_change_persists_reasoning_to_memory():
    memory = DummyMemoryManager()
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=DummyNotification(),
        llm_service=DummyLLM(),
        memory_manager=memory,
    )

    # Simplify generation steps
    service._generate_thesis = lambda change: "thesis"
    service._generate_antithesis = lambda change: "antithesis"
    service._generate_arguments = lambda change, thesis, antithesis: []
    service._generate_synthesis = lambda change, arguments: "synthesis"
    service._generate_conclusion_and_recommendation = lambda change, syn: (
        "conclusion",
        "recommendation",
    )

    change = RequirementChange(requirement_id=uuid4(), created_by="user")
    service.evaluate_change(change)

    assert memory.calls
    assert memory.calls[0][1] == MemoryType.DIALECTICAL_REASONING


def test_create_session_adds_welcome_message():
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=DummyNotification(),
        llm_service=DummyLLM(),
        memory_manager=DummyMemoryManager(),
    )

    session = service.create_session("alice")

    assert session.user_id == "alice"
    assert session.messages
    assert session.messages[0].sender == "system"


def test_process_message_records_conversation():
    chat_repo = ChatRepositoryInterface()
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=chat_repo,
        notification_service=DummyNotification(),
        llm_service=DummyLLM(),
        memory_manager=DummyMemoryManager(),
    )

    session = service.create_session("bob")
    response = service.process_message(session.id, "Hello", "bob")

    assert response.sender == "system"
    messages = chat_repo.get_messages_for_session(session.id)
    assert len(messages) >= 2
