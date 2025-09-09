"""Property-based tests for the reasoning loop convergence.

Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
"""

import importlib
from unittest.mock import MagicMock

import pytest

try:
    from hypothesis import given
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

reasoning_loop_module = importlib.import_module(
    "devsynth.methodology.edrr.reasoning_loop"
)


@pytest.mark.property
@pytest.mark.medium
def test_reasoning_loop_stops_on_completion(monkeypatch):
    """Loop halts on the first completed status.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    @given(
        st.lists(st.sampled_from(["in_progress", "completed"]), min_size=1, max_size=5)
    )
    def check(statuses):
        call_index = {"i": 0}

        def fake_apply(team, task, critic, memory):
            status = (
                statuses[call_index["i"]]
                if call_index["i"] < len(statuses)
                else "in_progress"
            )
            call_index["i"] += 1
            return {"status": status}

        monkeypatch.setattr(
            reasoning_loop_module,
            "_apply_dialectical_reasoning",
            fake_apply,
        )

        results = reasoning_loop_module.reasoning_loop(
            MagicMock(), {}, MagicMock(), max_iterations=len(statuses)
        )

        expected = (
            statuses.index("completed") + 1
            if "completed" in statuses
            else len(statuses)
        )
        assert len(results) == expected
        if "completed" in statuses:
            assert results[-1]["status"] == "completed"

    check()


@pytest.mark.property
@pytest.mark.medium
def test_reasoning_loop_respects_max_iterations(monkeypatch):
    """Loop runs at most max_iterations times.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    @given(st.integers(min_value=1, max_value=5))
    def check(max_iterations):
        def fake_apply(team, task, critic, memory):
            return {"status": "in_progress"}

        monkeypatch.setattr(
            reasoning_loop_module,
            "_apply_dialectical_reasoning",
            fake_apply,
        )

        results = reasoning_loop_module.reasoning_loop(
            MagicMock(), {}, MagicMock(), max_iterations=max_iterations
        )

        assert len(results) == max_iterations

    check()
