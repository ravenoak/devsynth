"""Targeted fast unit tests for reasoning_loop branch coverage."""

from __future__ import annotations

import itertools
import sys
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.domain.models.wsde_dialectical import DialecticalSequence
from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam
from devsynth.methodology.edrr.reasoning_loop import Phase


@pytest.mark.fast
@pytest.mark.unit
def test_import_accessor_returns_typed_apply() -> None:
    """The module-level helper exposes the canonical typed_apply callable."""

    accessor = rl._import_apply_dialectical_reasoning()

    assert accessor is rl.typed_apply


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_seeds_random_and_numpy_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deterministic seeding propagates to random and numpy random modules."""

    random_seed_calls: list[int] = []
    fake_random = types.ModuleType("random")

    def capture_random_seed(value: int) -> None:
        random_seed_calls.append(value)

    fake_random.seed = capture_random_seed  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "random", fake_random)

    numpy_seed_calls: list[int] = []
    fake_numpy = types.ModuleType("numpy")
    fake_numpy_random = types.ModuleType("numpy.random")

    def capture_numpy_seed(value: int) -> None:
        numpy_seed_calls.append(value)

    fake_numpy_random.seed = capture_numpy_seed  # type: ignore[attr-defined]
    fake_numpy.random = fake_numpy_random  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "numpy.random", fake_numpy_random)

    def fake_apply(
        team: Any, task: Any, critic: Any, memory_integration: Any
    ) -> dict[str, Any]:
        return {"status": "completed"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    results = rl.reasoning_loop(
        MagicMock(), {"solution": "initial"}, MagicMock(), deterministic_seed=42
    )

    assert results == [{"status": "completed"}]
    assert random_seed_calls == [42]
    assert numpy_seed_calls == [42]


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_logs_backoff_and_retry_exhaustion(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Transient errors trigger retry backoff logging and eventual exhaustion."""

    attempt_counter = {"count": 0}

    def failing_apply(*args: Any, **kwargs: Any) -> dict[str, Any]:
        attempt_counter["count"] += 1
        raise RuntimeError("boom")

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: failing_apply
    )

    sleep_intervals: list[float] = []
    monkeypatch.setattr(
        rl.time, "sleep", lambda duration: sleep_intervals.append(duration)
    )

    caplog.set_level("DEBUG", logger=rl.logger.logger.name)

    results = rl.reasoning_loop(
        MagicMock(),
        {"solution": "initial"},
        MagicMock(),
        retry_attempts=2,
        retry_backoff=0.1,
    )

    assert results == []
    assert attempt_counter["count"] == 3
    assert sleep_intervals == [0.1, 0.2]
    assert any(
        "Transient error in reasoning step; retrying in" in record.message
        for record in caplog.records
    )
    assert any(
        "Giving up after retries due to transient errors" in record.message
        for record in caplog.records
    )


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_coordinator_records_each_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Coordinator receives phase-specific records for expand/differentiate/refine."""

    payloads = [
        {"status": "in_progress", "phase": "expand", "next_phase": "differentiate"},
        {"status": "in_progress", "phase": "differentiate", "next_phase": "refine"},
        {"status": "completed", "phase": "refine"},
    ]
    payload_iter = iter(payloads)

    def fake_apply(
        team: Any, task: Any, critic: Any, memory_integration: Any
    ) -> dict[str, Any]:
        return next(payload_iter)

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    class RecordingCoordinator:
        def __init__(self) -> None:
            self.calls: list[tuple[Phase, dict[str, Any]]] = []

        def record_expand_results(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.calls.append((Phase.EXPAND, payload))
            return payload

        def record_differentiate_results(
            self, payload: dict[str, Any]
        ) -> dict[str, Any]:
            self.calls.append((Phase.DIFFERENTIATE, payload))
            return payload

        def record_refine_results(self, payload: dict[str, Any]) -> dict[str, Any]:
            self.calls.append((Phase.REFINE, payload))
            return payload

        def record_consensus_failure(
            self, exc: Exception
        ) -> None:  # pragma: no cover - unused
            raise AssertionError(
                "Consensus failure should not be recorded in this scenario"
            )

    coordinator = RecordingCoordinator()

    results = rl.reasoning_loop(
        MagicMock(),
        {"solution": "initial"},
        MagicMock(),
        coordinator=coordinator,
        phase=Phase.EXPAND,
    )

    assert len(results) == 3
    assert [phase for phase, _ in coordinator.calls] == [
        Phase.EXPAND,
        Phase.DIFFERENTIATE,
        Phase.REFINE,
    ]


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_exits_when_total_budget_elapsed(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Loop halts before work begins when the total time budget is exhausted."""

    monotonic_values = itertools.chain([0.0, 1.0], itertools.repeat(1.0))
    monkeypatch.setattr(rl.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(rl.time, "sleep", lambda _: None)

    def unexpected_apply(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError(
            "apply_dialectical_reasoning should not be invoked when budget exhausted"
        )

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: unexpected_apply
    )

    caplog.set_level("DEBUG", logger=rl.logger.logger.name)

    results = rl.reasoning_loop(
        MagicMock(), {"solution": "initial"}, MagicMock(), max_total_seconds=0.5
    )

    assert results == []
    assert any(
        "max_total_seconds budget" in record.message for record in caplog.records
    )


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_accepts_dialectical_sequence_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DialecticalSequence instances pass through the loop without conversion."""

    sequence = DialecticalSequence(sequence_id="seq-1", steps=())

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: lambda *_: sequence)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "sequence"},
        critic_agent=None,
    )

    assert results == [sequence]


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_records_unknown_phase_and_next_phase_fallbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown phase strings preserve the current phase and coordinator telemetry."""

    payloads = iter(
        [
            {
                "status": "in_progress",
                "phase": "mystery",
                "next_phase": "???",
            },
            {
                "status": "in_progress",
                "phase": "differentiate",
            },
            {"status": "completed", "phase": "refine"},
        ]
    )

    def fake_apply(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return next(payloads)

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    coordinator = CoordinatorRecorder()

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "phase"},
        critic_agent=None,
        coordinator=coordinator,
        phase=Phase.EXPAND,
        max_iterations=4,
    )

    assert len(results) == 3
    assert [record[0] for record in coordinator.records] == [
        "expand",
        "differentiate",
        "refine",
    ]
