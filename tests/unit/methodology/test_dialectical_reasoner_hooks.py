from uuid import uuid4

import pytest

from devsynth.application.requirements.dialectical_reasoner import (
    ConsensusError,
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


def _build_service(response: str) -> DialecticalReasonerService:
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=DummyNotification(),
        llm_service=DummyLLM(response),
    )
    service._generate_thesis = lambda change: "t"
    service._generate_antithesis = lambda change: "a"
    service._generate_arguments = lambda change, t, a: []
    service._generate_synthesis = lambda change, args: "s"
    service._generate_conclusion_and_recommendation = lambda change, syn: ("c", "r")
    return service


@pytest.mark.medium
def test_hook_receives_consensus_flag():
    service = _build_service("yes")
    change = RequirementChange(requirement_id=uuid4(), created_by="user")
    called = {}

    def hook(reasoning, consensus):
        called["id"] = reasoning.change_id
        called["consensus"] = consensus

    service.register_evaluation_hook(hook)
    reasoning = service.evaluate_change(change)

    assert called["consensus"] is True
    assert called["id"] == change.id
    assert reasoning.conclusion == "c"


@pytest.mark.medium
def test_hook_runs_on_failure():
    service = _build_service("no")
    change = RequirementChange(requirement_id=uuid4(), created_by="user")
    called = {}

    def hook(reasoning, consensus):
        called["consensus"] = consensus

    service.register_evaluation_hook(hook)
    with pytest.raises(ConsensusError):
        service.evaluate_change(change)

    assert called["consensus"] is False


@pytest.mark.medium
def test_hook_exception_suppressed(caplog):
    service = _build_service("yes")
    change = RequirementChange(requirement_id=uuid4(), created_by="user")

    def bad_hook(reasoning, consensus):
        raise RuntimeError("boom")

    service.register_evaluation_hook(bad_hook)
    with caplog.at_level("WARNING"):
        service.evaluate_change(change)

    assert "Evaluation hook failed" in caplog.text
