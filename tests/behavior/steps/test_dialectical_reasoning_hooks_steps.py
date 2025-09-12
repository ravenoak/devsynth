from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when

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

pytestmark = pytest.mark.fast
scenarios("../features/dialectical_reasoning.feature")


class _DummyNotification:
    def notify_change_proposed(self, change):
        pass

    def notify_change_approved(self, change):
        pass

    def notify_change_rejected(self, change):
        pass

    def notify_impact_assessment_completed(self, assessment):
        pass


class _DummyLLM:
    def query(self, prompt: str) -> str:
        return "yes"


@pytest.fixture
def context():
    return {}


@given("a dialectical reasoner with a registered hook")
def build_reasoner(context):
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=_DummyNotification(),
        llm_service=_DummyLLM(),
    )
    service._generate_thesis = lambda change: "t"
    service._generate_antithesis = lambda change: "a"
    service._generate_arguments = lambda change, t, a: []
    service._generate_synthesis = lambda change, args: "s"
    service._generate_conclusion_and_recommendation = lambda change, syn: ("c", "r")
    called = {}

    def hook(reasoning, consensus):
        called["id"] = reasoning.change_id
        called["consensus"] = consensus

    service.register_evaluation_hook(hook)
    context["service"] = service
    context["called"] = called


@when("I evaluate a change that reaches consensus")
def evaluate_change(context):
    change = RequirementChange(requirement_id=uuid4(), created_by="tester")
    context["reasoning"] = context["service"].evaluate_change(change)


@then("the hook should receive the reasoning and consensus flag")
def hook_called(context):
    assert context["called"]["consensus"] is True
    assert context["called"]["id"] == context["reasoning"].change_id
