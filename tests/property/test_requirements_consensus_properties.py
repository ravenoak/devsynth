"""Property-based tests for requirement consensus utilities.

Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
"""

import time
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from devsynth.domain.models.requirement import Requirement
from devsynth.domain.models.wsde_dialectical import (
    DialecticalSequence,
    apply_dialectical_reasoning,
)
from tests.helpers.dummies import _DummyTeam

from .strategies import consensus_outcome_strategy, requirement_strategy


@pytest.mark.property
@pytest.mark.medium
@settings(deadline=300)  # 300ms per example to keep CI stable
@given(req=requirement_strategy())
def test_requirement_update_timestamp_is_monotonic(req: Requirement):
    """Updating a requirement should not regress its timestamp.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """
    before = req.updated_at
    req.update(title=req.title + "!")
    after = req.updated_at

    assert after >= before, "updated_at should be monotonically non-decreasing"


class _DummyCritic:
    name = "critic"

    def critique(self, *_args, **_kwargs):  # not used by current implementation
        return {"notes": "ok"}


@pytest.mark.property
@pytest.mark.fast
@settings(max_examples=10, deadline=500)
@given(thesis_content=st.text(min_size=5, max_size=80))
@pytest.mark.no_network
def test_dialectical_reasoning_returns_expected_shape_quickly(thesis_content: str):
    """dialectical reasoning yields expected keys quickly.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """
    team = _DummyTeam()
    task: dict[str, Any] = {
        "solution": {"content": thesis_content, "code": "x=1\nprint(x)"}
    }
    critic = _DummyCritic()

    start = time.perf_counter()
    result = apply_dialectical_reasoning(team, task, critic, memory_integration=None)
    elapsed = time.perf_counter() - start

    # Shape assertions
    assert isinstance(result, DialecticalSequence)
    payload = result.to_dict()
    for key in (
        "id",
        "timestamp",
        "task_id",
        "thesis",
        "antithesis",
        "synthesis",
        "method",
    ):
        assert key in payload, f"missing key: {key}"
    assert payload["method"] == "dialectical_reasoning"

    # Time bound: keep very generous to remain stable across CI runners
    assert (
        elapsed < 0.5
    ), f"dialectical reasoning should be fast for simple input, took {elapsed:.3f}s"


@pytest.mark.property
@pytest.mark.medium
@settings(max_examples=5, deadline=300)
@given(outcome=consensus_outcome_strategy())
def test_generated_consensus_outcome_has_expected_keys(outcome: dict[str, Any]):
    """Generated consensus outcomes provide required keys.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """
    for key in (
        "id",
        "task_id",
        "timestamp",
        "thesis",
        "antithesis",
        "synthesis",
        "method",
    ):
        assert key in outcome
    assert isinstance(outcome["id"], str)
    assert isinstance(outcome["task_id"], str)
    assert hasattr(outcome["timestamp"], "isoformat")
    assert isinstance(outcome["thesis"], dict)
    assert isinstance(outcome["antithesis"], dict)
    assert isinstance(outcome["synthesis"], dict)
    assert outcome["method"] == "dialectical_reasoning"
