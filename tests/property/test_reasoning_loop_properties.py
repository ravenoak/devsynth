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

from devsynth.methodology.base import Phase

reasoning_loop_module = importlib.import_module(
    "devsynth.methodology.edrr.reasoning_loop",
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
    @pytest.mark.property
    @pytest.mark.medium
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

    @pytest.mark.property
    @pytest.mark.medium
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


@pytest.mark.property
@pytest.mark.medium
def test_reasoning_loop_phase_transitions(monkeypatch):
    """Loop advances according to `next_phase` or fallback map.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    @given(
        st.lists(
            st.one_of(st.none(), st.sampled_from(list(Phase))),
            min_size=1,
            max_size=5,
        )
    )
    @pytest.mark.property
    @pytest.mark.medium
    def check(next_phases):
        phase_map = {
            Phase.EXPAND: Phase.DIFFERENTIATE,
            Phase.DIFFERENTIATE: Phase.REFINE,
            Phase.REFINE: Phase.REFINE,
        }
        current = Phase.EXPAND
        expected: list[Phase] = []
        results = []
        for idx, np_phase in enumerate(next_phases):
            expected.append(current)
            result = {
                "status": "completed" if idx == len(next_phases) - 1 else "in_progress",
                "phase": current.value,
            }
            if np_phase is not None:
                result["next_phase"] = np_phase.value
                current = np_phase
            else:
                current = phase_map[current]
            results.append(result)

        call_idx = {"i": 0}

        def fake_apply(team, task, critic, memory):
            res = results[call_idx["i"]]
            call_idx["i"] += 1
            return res

        monkeypatch.setattr(
            reasoning_loop_module,
            "_apply_dialectical_reasoning",
            fake_apply,
        )

        recorded: list[Phase] = []

        class Recorder:
            def record_expand_results(self, result):
                recorded.append(Phase.EXPAND)
                return result

            def record_differentiate_results(self, result):
                recorded.append(Phase.DIFFERENTIATE)
                return result

            def record_refine_results(self, result):
                recorded.append(Phase.REFINE)
                return result

        reasoning_loop_module.reasoning_loop(
            MagicMock(),
            {},
            MagicMock(),
            coordinator=Recorder(),
            phase=Phase.EXPAND,
            max_iterations=len(next_phases),
        )

        assert recorded == expected

    check()
