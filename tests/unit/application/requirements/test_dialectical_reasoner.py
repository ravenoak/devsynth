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
from devsynth.domain.models.requirement import RequirementChange


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
    def __init__(self, response: str):
        self.response = response

    def query(self, prompt: str) -> str:
        return self.response


def _build_service(llm_response: str) -> DialecticalReasonerService:
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=DummyNotification(),
        llm_service=DummyLLM(llm_response),
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
