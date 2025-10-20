"""Strengthened EDRR reasoning loop scenarios for budgets and error propagation."""

# Strengthened EDRR reasoning loop scenarios for budgets and fallbacks.

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam
from devsynth.methodology.edrr.reasoning_loop import Phase

rl = importlib.import_module("devsynth.methodology.edrr.reasoning_loop")


@pytest.mark.fast
def test_import_helper_exposes_typed_apply() -> None:
    """ReqID: EDRR-LOOP-Import-00 — Internal accessor returns the typed callable."""

    assert rl._import_apply_dialectical_reasoning() is rl.typed_apply


@pytest.mark.fast
def test_reasoning_loop_immediate_timeout_skips_apply_invocation(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: EDRR-LOOP-Timeout-02 — Guard exits before invoking the reasoning step."""

    monotonic_values = iter([0.0, 1.0])

    def fake_monotonic() -> float:
        try:
            return next(monotonic_values)
        except StopIteration:  # pragma: no cover - deterministic guard
            return 1.0

    apply_spy = MagicMock(
        side_effect=AssertionError("reasoning callable should not be reached")
    )

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: apply_spy)

    caplog.set_level("DEBUG", rl.logger.logger.name)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"prompt": "timeout"},
        critic_agent=None,
        max_total_seconds=0.5,
    )

    assert results == []
    apply_spy.assert_not_called()
    assert any(
        "max_total_seconds budget" in record.message for record in caplog.records
    )


@pytest.mark.fast
def test_reasoning_loop_respects_total_budget_and_emits_debug(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: EDRR-LOOP-Timeout-01 — Total budget stops iterations with telemetry."""

    clock = {"value": 0.0}

    def fake_monotonic() -> float:
        return clock["value"]

    def fake_apply(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        clock["value"] += 0.25
        return {"status": "in_progress", "phase": "refine"}

    logger_spy = MagicMock()

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)
    monkeypatch.setattr(rl, "logger", logger_spy)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={},
        critic_agent=None,
        max_iterations=4,
        max_total_seconds=0.2,
    )

    assert results == [{"status": "in_progress", "phase": "refine"}]
    assert any(
        "max_total_seconds budget" in call.args[0]
        for call in logger_spy.debug.call_args_list
    )


@pytest.mark.fast
def test_reasoning_loop_uses_fallback_after_invalid_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: EDRR-LOOP-Phase-02 — Invalid phases fall back to deterministic transitions."""

    payloads = [
        {"status": "in_progress", "phase": "mystery", "next_phase": "differentiate"},
        {"status": "completed"},
    ]
    calls = {"index": 0}

    def fake_apply(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        value = payloads[calls["index"]]
        calls["index"] += 1
        return value

    coordinator = CoordinatorRecorder()

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={},
        critic_agent=None,
        coordinator=coordinator,
        phase=Phase.EXPAND,
        max_iterations=3,
    )

    assert len(results) == 2
    assert [phase for phase, _ in coordinator.records] == ["expand", "differentiate"]


@pytest.mark.fast
def test_reasoning_loop_stops_after_retry_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: EDRR-LOOP-Error-03 — Exhausted retries propagate stop conditions."""

    calls = {"count": 0}

    def flaky_apply(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["count"] += 1
        if calls["count"] == 1:
            return {"status": "in_progress", "phase": "refine"}
        raise RuntimeError("boom")

    logger_spy = MagicMock()

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: flaky_apply)
    monkeypatch.setattr(rl.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(rl, "logger", logger_spy)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={},
        critic_agent=None,
        max_iterations=3,
        retry_attempts=1,
        retry_backoff=0.05,
    )

    assert results == [{"status": "in_progress", "phase": "refine"}]
    assert calls["count"] == 3
    messages = [call.args[0] for call in logger_spy.debug.call_args_list]
    assert any("Transient error" in message for message in messages)
    assert any("Giving up after retries" in message for message in messages)


@pytest.mark.fast
def test_reasoning_loop_seeds_random_and_numpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """ReqID: EDRR-LOOP-Seed-04 — Deterministic seeding configures random providers."""

    import random as real_random

    seed_spy = MagicMock()
    monkeypatch.setattr(real_random, "seed", seed_spy)

    original_import_module = importlib.import_module
    fake_numpy_random = MagicMock()

    def fake_import_module(name: str, package: str | None = None):
        if name == "numpy.random":
            return fake_numpy_random
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    def single_run(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"status": "completed", "phase": "refine"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: single_run)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"prompt": "seeded"},
        critic_agent=None,
        deterministic_seed=123,
    )

    assert results == [{"status": "completed", "phase": "refine"}]
    seed_spy.assert_called_once_with(123)
    fake_numpy_random.seed.assert_called_once_with(123)


@pytest.mark.fast
def test_reasoning_loop_applies_synthesis_to_task(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ReqID: EDRR-LOOP-Synthesis-05 — Synthesis payload updates the working task."""

    class TaskRecorder:
        def __init__(self) -> None:
            self.syntheses: list[dict[str, Any]] = []

        def with_solution(self, synthesis: dict[str, Any]) -> "TaskRecorder":
            self.syntheses.append(synthesis)
            return self

    task_stub = TaskRecorder()

    payloads = [
        {
            "status": "in_progress",
            "phase": "expand",
            "synthesis": {"value": 1},
            "next_phase": "differentiate",
        },
        {"status": "completed"},
    ]
    calls = {"index": 0}

    def fake_apply(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        value = payloads[calls["index"]]
        calls["index"] += 1
        return value

    monkeypatch.setattr(rl, "ensure_dialectical_task", lambda _task: task_stub)
    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: fake_apply)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"prompt": "update"},
        critic_agent=None,
        phase=Phase.EXPAND,
        max_iterations=3,
    )

    assert len(results) == 2
    assert task_stub.syntheses == [{"value": 1}]
