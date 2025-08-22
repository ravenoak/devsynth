from uuid import uuid4

import pytest

from devsynth.domain.models.requirement import RequirementChange
from tests.unit.methodology.test_dialectical_reasoner_hooks import _build_service


@pytest.mark.fast
def test_evaluation_terminates_with_many_hooks():
    """Evaluation terminates with many hooks.

    ReqID: dialectical_reasoning-termination"""

    service = _build_service("yes")
    change = RequirementChange(requirement_id=uuid4(), created_by="user")
    count = 0

    def hook(_, __):
        nonlocal count
        count += 1

    for _ in range(1000):
        service.register_evaluation_hook(hook)

    service.evaluate_change(change)

    assert count == 1000


@pytest.mark.fast
def test_hooks_continue_after_exception():
    """Subsequent hooks run after an exception.

    ReqID: dialectical_reasoning-termination"""

    service = _build_service("yes")
    change = RequirementChange(requirement_id=uuid4(), created_by="user")
    calls = []

    def bad_hook(_, __):
        raise RuntimeError("boom")

    def good_hook(_, __):
        calls.append("good")

    service.register_evaluation_hook(bad_hook)
    service.register_evaluation_hook(good_hook)

    service.evaluate_change(change)

    assert calls == ["good"]
