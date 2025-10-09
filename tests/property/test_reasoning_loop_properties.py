"""Property-based tests for the reasoning loop convergence.

Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
"""

import importlib
import sys
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

try:
    from hypothesis import HealthCheck, example, given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.domain.models.wsde_facade import WSDETeam
from devsynth.methodology.base import Phase

reasoning_loop_module = importlib.import_module(
    "devsynth.methodology.edrr.reasoning_loop",
)


@pytest.mark.property
@pytest.mark.medium
@given(
    statuses=st.lists(
        st.sampled_from(["in_progress", "completed"]), min_size=1, max_size=5
    )
)
@example(statuses=["completed"])
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reasoning_loop_stops_on_completion(monkeypatch, statuses):
    """Loop halts on the first completed status.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

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
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(), {}, MagicMock(), max_iterations=len(statuses)
    )

    expected = (
        statuses.index("completed") + 1 if "completed" in statuses else len(statuses)
    )
    assert len(results) == expected
    if "completed" in statuses:
        assert results[-1]["status"] == "completed"


@pytest.mark.property
@pytest.mark.medium
@given(max_iterations=st.integers(min_value=1, max_value=5))
@example(max_iterations=1)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reasoning_loop_respects_max_iterations(monkeypatch, max_iterations):
    """Loop runs at most max_iterations times.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    def fake_apply(team, task, critic, memory):
        return {"status": "in_progress"}

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(), {}, MagicMock(), max_iterations=max_iterations
    )

    assert len(results) == max_iterations


def _normalized_phase_strings(phase: Phase) -> list[str]:
    return [phase.value, phase.value.upper(), phase.value.title()]


@st.composite
def dialectical_result_payloads(draw):
    base_phase = draw(
        st.sampled_from([Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE])
    )
    phase_value = draw(
        st.one_of(
            st.sampled_from(_normalized_phase_strings(base_phase)),
            st.sampled_from(["UNKNOWN", "", "???"]),
        )
    )
    status = draw(st.sampled_from(["in_progress", "completed"]))
    next_phase_value = draw(
        st.one_of(
            st.none(),
            st.sampled_from(
                [
                    token
                    for phase in [Phase.EXPAND, Phase.DIFFERENTIATE, Phase.REFINE]
                    for token in _normalized_phase_strings(phase)
                ]
            ),
            st.sampled_from(["invalid", "UNKNOWN", "", "???"]),
        )
    )
    synthesis = draw(st.text(min_size=1, max_size=5))
    payload: dict[str, Any] = {
        "status": status,
        "phase": phase_value,
        "synthesis": synthesis,
    }
    if next_phase_value is not None:
        payload["next_phase"] = next_phase_value

    if draw(st.booleans()):
        return DialecticalSequence.from_dict(payload)
    return payload


@pytest.mark.property
@pytest.mark.medium
@given(payloads=st.lists(dialectical_result_payloads(), min_size=1, max_size=5))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reasoning_loop_phase_transitions(monkeypatch, payloads):
    """Loop advances according to `next_phase` or fallback map.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    phase_transition = {
        Phase.EXPAND: Phase.DIFFERENTIATE,
        Phase.DIFFERENTIATE: Phase.REFINE,
        Phase.REFINE: Phase.REFINE,
    }

    expected_recorded: list[Phase] = []
    normalized_sequence_phases: list[Phase | None] = []
    fallback_expectations: dict[int, Phase] = {}
    current_phase = Phase.EXPAND

    for idx, payload in enumerate(payloads):
        mapping = dict(payload)
        result_phase_value = mapping.get("phase")
        effective_phase = current_phase
        normalized_phase: Phase | None = None
        if isinstance(result_phase_value, str):
            try:
                normalized_phase = Phase(result_phase_value.lower())
                effective_phase = normalized_phase
            except Exception:
                pass
        normalized_sequence_phases.append(normalized_phase)
        expected_recorded.append(effective_phase)

        next_phase_value = mapping.get("next_phase")
        fallback_phase = phase_transition.get(current_phase, current_phase)
        fallback_triggered = False
        if isinstance(next_phase_value, str):
            try:
                current_phase = Phase(next_phase_value.lower())
            except Exception:
                current_phase = fallback_phase
                fallback_triggered = True
        else:
            current_phase = fallback_phase
            fallback_triggered = True

        if fallback_triggered:
            fallback_expectations[idx + 1] = current_phase

        if mapping.get("status") == "completed":
            break

    call_idx = {"i": 0}

    def fake_apply(team, task, critic, memory):
        res = payloads[call_idx["i"]]
        call_idx["i"] += 1
        return res

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    recorded_calls: list[tuple[Phase, dict[str, Any]]] = []

    class Recorder:
        def record_expand_results(self, result):
            recorded_calls.append((Phase.EXPAND, result))
            return result

        def record_differentiate_results(self, result):
            recorded_calls.append((Phase.DIFFERENTIATE, result))
            return result

        def record_refine_results(self, result):
            recorded_calls.append((Phase.REFINE, result))
            return result

    reasoning_loop_module.reasoning_loop(
        MagicMock(),
        {},
        MagicMock(),
        coordinator=Recorder(),
        phase=Phase.EXPAND,
        max_iterations=len(payloads),
    )

    recorded_phases = [phase for phase, _ in recorded_calls]
    assert recorded_phases == expected_recorded[: len(recorded_phases)]

    for idx, (phase, _payload) in enumerate(recorded_calls):
        raw_payload = payloads[idx]
        if (
            isinstance(raw_payload, DialecticalSequence)
            and normalized_sequence_phases[idx] is not None
        ):
            assert phase == normalized_sequence_phases[idx]

        fallback_phase = fallback_expectations.get(idx)
        if fallback_phase is not None and normalized_sequence_phases[idx] is None:
            assert phase == fallback_phase


@pytest.mark.property
@pytest.mark.medium
@given(syntheses=st.lists(st.text(min_size=1), min_size=1, max_size=5))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reasoning_loop_propagates_synthesis(monkeypatch, syntheses):
    """Each synthesis becomes the next iteration's solution.

    Issue: issues/Finalize-dialectical-reasoning.md ReqID: DRL-001
    """

    call = {"i": 0}
    tasks: list[dict[str, Any]] = []

    def fake_apply(team, task, critic, memory):
        tasks.append(task.copy())
        idx = call["i"]
        status = "completed" if idx == len(syntheses) - 1 else "in_progress"
        call["i"] += 1
        return DialecticalSequence.from_dict(
            {"status": status, "synthesis": syntheses[idx]}
        )

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    reasoning_loop_module.reasoning_loop(
        MagicMock(), {}, MagicMock(), max_iterations=len(syntheses)
    )

    for i in range(1, len(tasks)):
        solution = tasks[i]["solution"]
        if isinstance(solution, dict):
            observed = solution.get("content", solution)
        else:
            observed = solution
        assert observed == syntheses[i - 1]


@pytest.mark.property
@pytest.mark.medium
@given(
    initial_solution=st.text(min_size=1, max_size=10),
    syntheses=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=4),
)
@example(initial_solution="init", syntheses=["done"])
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reasoning_loop_invokes_dialectical_hooks(
    monkeypatch, initial_solution, syntheses
):
    """Registered hooks observe each dialectical iteration.

    Issue: issues/dialectical_reasoning.md ReqID: DRL-001
    """

    statuses = ["in_progress"] * (len(syntheses) - 1) + ["completed"]
    team = WSDETeam("dialectical")
    recorded: list[tuple[str, str]] = []

    def hook(task, solutions):
        recorded.append((task["solution"], solutions[0]["synthesis"]))

    team.register_dialectical_hook(hook)

    call = {"i": 0}

    def fake_apply(wsde_team, task, critic, memory):
        idx = call["i"]
        result = DialecticalSequence.from_dict(
            {"status": statuses[idx], "synthesis": syntheses[idx]}
        )
        call["i"] += 1
        for hook_fn in getattr(wsde_team, "dialectical_hooks", []):
            hook_fn(task, [result])
        return result

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    task = {"solution": initial_solution}
    critic = object()
    results = reasoning_loop_module.reasoning_loop(
        team, task, critic, max_iterations=len(syntheses)
    )

    assert len(results) == len(syntheses)
    assert len(recorded) == len(results)
    expected_solutions = [initial_solution, *syntheses[:-1]]
    for idx, (task_solution, recorded_synthesis) in enumerate(recorded):
        if isinstance(task_solution, dict):
            observed_task_solution = task_solution.get("content", task_solution)
        else:
            observed_task_solution = task_solution
        assert observed_task_solution == expected_solutions[idx]
        if isinstance(recorded_synthesis, dict):
            recorded_value = recorded_synthesis.get("content", recorded_synthesis)
        else:
            recorded_value = recorded_synthesis
        assert recorded_value == syntheses[idx]


@pytest.mark.property
@pytest.mark.fast
@given(seed=st.integers(min_value=0, max_value=2**10 - 1))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_reasoning_loop_deterministic_seed_paths(monkeypatch, seed):
    """Both random and numpy random modules receive the deterministic seed."""

    fake_random = types.ModuleType("random")
    random_seed_calls = []

    def capture_random_seed(value):
        random_seed_calls.append(value)

    fake_random.seed = capture_random_seed  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "random", fake_random)

    fake_numpy = types.ModuleType("numpy")
    fake_numpy_random = types.ModuleType("numpy.random")
    numpy_seed_calls = []

    def capture_numpy_seed(value):
        numpy_seed_calls.append(value)

    fake_numpy_random.seed = capture_numpy_seed  # type: ignore[attr-defined]
    fake_numpy.random = fake_numpy_random  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "numpy.random", fake_numpy_random)

    def fake_apply(team, task, critic, memory):
        return {"status": "completed"}

    monkeypatch.setattr(
        reasoning_loop_module,
        "_import_apply_dialectical_reasoning",
        lambda: fake_apply,
    )

    results = reasoning_loop_module.reasoning_loop(
        MagicMock(), {"solution": "initial"}, MagicMock(), deterministic_seed=seed
    )

    assert results == [{"status": "completed"}]
    assert random_seed_calls == [seed]
    assert numpy_seed_calls == [seed]
