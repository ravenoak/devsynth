import time
from uuid import uuid4

import pytest

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
def test_termination_and_linear_complexity():
    """Evaluate complexity of hook execution.

    ReqID: dialectical_reasoning-termination
    """

    n = 1000
    change = RequirementChange(requirement_id=uuid4(), created_by="user")

    # First run with n hooks
    service = _build_service("yes")
    counter_n = [0]

    def make_hook(counter):
        def hook(reasoning, consensus):
            for _ in range(100):
                pass
            counter[0] += 1

        return hook

    hook_n = make_hook(counter_n)
    for _ in range(n):
        service.register_evaluation_hook(hook_n)

    start = time.perf_counter()
    service.evaluate_change(change)
    elapsed_n = time.perf_counter() - start
    assert counter_n[0] == n

    # Second run with 2n hooks
    service_2n = _build_service("yes")
    counter_2n = [0]
    hook_2n = make_hook(counter_2n)
    for _ in range(2 * n):
        service_2n.register_evaluation_hook(hook_2n)

    start = time.perf_counter()
    service_2n.evaluate_change(change)
    elapsed_2n = time.perf_counter() - start
    assert counter_2n[0] == 2 * n

    # Runtime should grow at most linearly with number of hooks
    assert elapsed_2n >= elapsed_n
    assert elapsed_2n < 4 * elapsed_n
