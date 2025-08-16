from uuid import uuid4

import pytest

from devsynth.application.collaboration.exceptions import ConsensusError
from devsynth.application.requirements.dialectical_reasoner import (
    DialecticalReasonerService,
)
from devsynth.domain.interfaces.requirement import (
    ChatRepositoryInterface,
    DialecticalReasoningRepositoryInterface,
    ImpactAssessmentRepositoryInterface,
    RequirementRepositoryInterface,
)
from devsynth.domain.models.memory import MemoryType
from devsynth.domain.models.requirement import (
    ChangeType,
    Requirement,
    RequirementChange,
)


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
    def __init__(self, response):
        self.response = response

    def query(self, prompt: str):
        return self.response


class DummyMemoryManager:
    def __init__(self):
        self.calls = []

    def store_with_edrr_phase(self, content, memory_type, edrr_phase, metadata=None):
        self.calls.append((content, memory_type, edrr_phase, metadata))
        return "mem-id"


def _build_service(
    llm_response: str, memory_manager=None
) -> DialecticalReasonerService:
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=DummyNotification(),
        llm_service=DummyLLM(llm_response),
        memory_manager=memory_manager,
    )

    # Simplify generation steps to isolate consensus logic
    service._generate_thesis = lambda change: "thesis"
    service._generate_antithesis = lambda change: "antithesis"
    service._generate_arguments = lambda change, thesis, antithesis: []
    service._generate_synthesis = lambda change, arguments: "synthesis"
    service._generate_conclusion_and_recommendation = lambda change, syn: (
        "conclusion",
        "recommendation",
    )
    return service


def test_evaluate_change_reaches_consensus():
    service = _build_service("yes")
    change = RequirementChange(requirement_id=uuid4(), created_by="alice")

    reasoning = service.evaluate_change(change)

    assert reasoning.conclusion == "conclusion"
    # Ensure reasoning persisted only when consensus reached
    assert service.reasoning_repository.get_reasoning(reasoning.id) is not None


def test_evaluate_change_logs_consensus_failure(caplog):
    service = _build_service("no")
    change = RequirementChange(requirement_id=uuid4(), created_by="bob")

    with caplog.at_level("ERROR"), pytest.raises(ConsensusError):
        service.evaluate_change(change)

    assert "Consensus not reached" in caplog.text
    assert not service.reasoning_repository.reasonings


def test_evaluate_change_stores_with_phase():
    memory = DummyMemoryManager()
    service = _build_service("yes", memory_manager=memory)
    change = RequirementChange(requirement_id=uuid4(), created_by="carol")

    service.evaluate_change(change, edrr_phase="EXPAND")

    assert memory.calls
    assert memory.calls[0][1] == MemoryType.DIALECTICAL_REASONING
    assert memory.calls[0][2] == "EXPAND"


def test_evaluate_change_failure_stores_retrospect():
    memory = DummyMemoryManager()
    service = _build_service("no", memory_manager=memory)
    change = RequirementChange(requirement_id=uuid4(), created_by="dave")

    with pytest.raises(ConsensusError):
        service.evaluate_change(change, edrr_phase="EXPAND")

    assert memory.calls
    assert memory.calls[0][2] == "RETROSPECT"


def test_evaluation_hook_receives_consensus():
    service = _build_service("yes")
    change = RequirementChange(requirement_id=uuid4(), created_by="eve")

    called = {}

    def hook(reasoning, consensus):
        called["consensus"] = consensus
        called["id"] = reasoning.change_id

    service.register_evaluation_hook(hook)
    service.evaluate_change(change)

    assert called["consensus"] is True
    assert called["id"] == change.id


def test_evaluation_hook_runs_on_failure():
    service = _build_service("no")
    change = RequirementChange(requirement_id=uuid4(), created_by="frank")

    called = {}

    def hook(reasoning, consensus):
        called["consensus"] = consensus

    service.register_evaluation_hook(hook)
    with pytest.raises(ConsensusError):
        service.evaluate_change(change)

    assert called["consensus"] is False


def test_evaluate_change_non_text_response_errors():
    service = _build_service({"answer": "yes"})
    change = RequirementChange(requirement_id=uuid4(), created_by="grace")

    with pytest.raises(ConsensusError):
        service.evaluate_change(change)


def test_evaluate_change_invalid_response_errors():
    service = _build_service("maybe")
    change = RequirementChange(requirement_id=uuid4(), created_by="heidi")

    with pytest.raises(ConsensusError):
        service.evaluate_change(change)


def test_assess_impact_stores_with_phase():
    memory = DummyMemoryManager()
    service = _build_service("yes", memory_manager=memory)
    new_req = Requirement(title="title", description="desc", created_by="erin")
    change = RequirementChange(
        requirement_id=uuid4(),
        change_type=ChangeType.ADD,
        new_state=new_req,
        created_by="erin",
    )

    service.assess_impact(change, edrr_phase="RETROSPECT")

    assert memory.calls
    assert memory.calls[0][1] == MemoryType.DOCUMENTATION
    assert memory.calls[0][2] == "RETROSPECT"
