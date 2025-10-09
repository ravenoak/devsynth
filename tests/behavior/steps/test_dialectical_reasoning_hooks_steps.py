from uuid import uuid4

import pytest
from pytest_bdd import given, scenarios, then, when

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
from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast
scenarios(feature_path(__file__, "general", "dialectical_reasoning.feature"))


class _DummyNotification:
    def notify_change_proposed(self, payload):
        pass

    def notify_change_approved(self, payload):
        pass

    def notify_change_rejected(self, payload):
        pass

    def notify_impact_assessment_completed(self, payload):
        pass


class _DummyLLM:
    def __init__(self, response: str = "yes") -> None:
        self.response = response

    def query(self, prompt: str) -> str:
        return self.response


@pytest.fixture
def context():
    return {}


@given("a dialectical reasoner with a registered hook")
def build_reasoner(context):
    llm = _DummyLLM()
    service = DialecticalReasonerService(
        requirement_repository=RequirementRepositoryInterface(),
        reasoning_repository=DialecticalReasoningRepositoryInterface(),
        impact_repository=ImpactAssessmentRepositoryInterface(),
        chat_repository=ChatRepositoryInterface(),
        notification_service=_DummyNotification(),
        llm_service=llm,
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
    context["llm"] = llm
    context["expected_consensus"] = True
    context["reasoning"] = None
    context["error"] = None


@given("the evaluation outcome will reach consensus")
def configure_consensus(context):
    context["llm"].response = "yes"
    context["expected_consensus"] = True


@given("the evaluation outcome will fail to reach consensus")
def configure_failure(context):
    context["llm"].response = "no"
    context["expected_consensus"] = False


@when("I evaluate the change")
def evaluate_change(context):
    change = RequirementChange(requirement_id=uuid4(), created_by="tester")
    context["change"] = change
    try:
        context["reasoning"] = context["service"].evaluate_change(change)
        context["error"] = None
    except ConsensusError as exc:
        context["reasoning"] = None
        context["error"] = exc


@then("the hook should record the evaluation outcome")
def hook_called(context):
    expected = context["expected_consensus"]
    assert context["called"]["consensus"] is expected
    if expected:
        assert context["error"] is None
        assert context["reasoning"] is not None
        assert context["called"]["id"] == context["reasoning"].change_id
    else:
        assert context["error"] is not None
        assert context["called"]["id"] == context["change"].id
