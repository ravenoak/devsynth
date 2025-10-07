"""Additional branch coverage for the EDRR reasoning loop."""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from typing import Any

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl


class DummyTeam:
    """Minimal WSDETeamProtocol double for reasoning loop tests."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "DummyTeam()"


class DummyCoordinator:
    """Coordinator double that captures per-phase recording payloads."""

    def __init__(self) -> None:
        self.expand_calls: list[dict[str, Any]] = []
        self.differentiate_calls: list[dict[str, Any]] = []
        self.refine_calls: list[dict[str, Any]] = []

    def record_expand_results(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.expand_calls.append(payload)
        return payload

    def record_differentiate_results(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.differentiate_calls.append(payload)
        return payload

    def record_refine_results(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.refine_calls.append(payload)
        return payload

    def record_consensus_failure(self, exc: BaseException) -> None:  # pragma: no cover - not used
        raise AssertionError(f"Unexpected consensus failure: {exc!r}")


def _cycle(values: list[Any]) -> Iterator[Any]:
    """Yield values sequentially, repeating the last one when exhausted."""

    index = 0
    while True:
        if index < len(values):
            yield values[index]
            index += 1
        else:
            yield values[-1]


@pytest.mark.fast
def test_reasoning_loop_deterministic_seed_influences_random_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure deterministic seeding touches `random` and `numpy.random`."""

    seed_calls: list[int] = []

    import random

    monkeypatch.setattr(random, "seed", lambda value: seed_calls.append(value))

    numpy_calls: list[int] = []
    fake_numpy_random = types.SimpleNamespace(seed=lambda value: numpy_calls.append(value))
    monkeypatch.setitem(sys.modules, "numpy.random", fake_numpy_random)

    def fake_apply(*_: Any, **__: Any) -> dict[str, Any]:
        return {"status": "completed"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    rl.reasoning_loop(
        DummyTeam(),
        {"solution": "seed"},
        critic_agent=None,
        deterministic_seed=7,
    )

    assert seed_calls == [7]
    assert numpy_calls == [7]


@pytest.mark.fast
def test_reasoning_loop_retry_exhaustion_logs_and_backs_off(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Transient exceptions exhaust retries, log debug telemetry, and back off exponentially."""

    attempts: list[int] = []

    def fake_apply(*_: Any, **__: Any) -> dict[str, Any]:
        attempts.append(len(attempts))
        raise RuntimeError("transient failure")

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    sleep_calls: list[float] = []
    monkeypatch.setattr(rl.time, "sleep", sleep_calls.append)

    caplog.set_level("DEBUG", logger=rl.logger.logger.name)

    results = rl.reasoning_loop(
        DummyTeam(),
        {"solution": "retry"},
        critic_agent=None,
        retry_attempts=2,
        retry_backoff=0.5,
    )

    assert results == []
    assert sleep_calls == [0.5, 1.0]
    assert "Giving up after retries due to transient errors" in caplog.messages[-1]


@pytest.mark.fast
def test_reasoning_loop_coordinator_records_per_phase(monkeypatch: pytest.MonkeyPatch) -> None:
    """The coordinator receives copies of payloads keyed to each reported phase."""

    coordinator = DummyCoordinator()

    payloads = [
        {"status": "pending", "phase": "expand", "next_phase": "differentiate"},
        {"status": "pending", "phase": "differentiate", "next_phase": "refine"},
        {"status": "completed", "phase": "refine"},
    ]

    call_iter = iter(payloads)

    def fake_apply(*_: Any, **__: Any) -> dict[str, Any]:
        return next(call_iter)

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    results = rl.reasoning_loop(
        DummyTeam(),
        {"solution": "phased"},
        critic_agent=None,
        coordinator=coordinator,
        max_iterations=len(payloads),
    )

    assert results == payloads
    assert coordinator.expand_calls == [payloads[0]]
    assert coordinator.differentiate_calls == [payloads[1]]
    assert coordinator.refine_calls == [payloads[2]]


@pytest.mark.fast
def test_reasoning_loop_halts_when_total_budget_consumed(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """When the total budget expires, the loop exits before invoking reasoning."""

    caplog.set_level("DEBUG", logger=rl.logger.logger.name)

    monotonic_values = _cycle([0.0, 2.0])
    monkeypatch.setattr(rl.time, "monotonic", lambda: next(monotonic_values))

    def fake_apply(*_: Any, **__: Any) -> dict[str, Any]:  # pragma: no cover - should not run
        raise AssertionError("apply_dialectical_reasoning should not be invoked when budget exhausted")

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    results = rl.reasoning_loop(
        DummyTeam(),
        {"solution": "budget"},
        critic_agent=None,
        max_total_seconds=1.0,
    )

    assert results == []
    assert "reasoning_loop exiting due to max_total_seconds budget" in caplog.messages[0]

