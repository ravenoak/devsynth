from __future__ import annotations

import importlib
import random
from typing import Any

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.methodology.edrr.contracts import NullWSDETeam


@pytest.mark.fast
def test_reasoning_loop_handles_seed_failures_gracefully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deterministic seeding failures should not break the reasoning loop."""

    random_calls: list[int] = []

    def failing_seed(value: int) -> None:
        random_calls.append(value)
        raise RuntimeError("rng backend unavailable")

    monkeypatch.setattr(random, "seed", failing_seed)

    imported_modules: list[str] = []

    def failing_import(module: str, package: str | None = None) -> Any:
        imported_modules.append(module)
        raise ImportError(module)

    monkeypatch.setattr(importlib, "import_module", failing_import)

    def completes_once(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"status": "completed", "phase": "refine"}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: completes_once
    )

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "demo"},
        critic_agent=None,
        deterministic_seed=2025,
    )

    assert results == [{"status": "completed", "phase": "refine"}]
    assert random_calls == [2025]
    assert imported_modules == ["numpy.random"]


@pytest.mark.fast
def test_reasoning_loop_logs_retry_exhaustion(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Retry exhaustion should emit a debug log and stop the loop."""

    attempt_counter = {"value": 0}

    def always_fail(*_args: Any, **_kwargs: Any) -> None:
        attempt_counter["value"] += 1
        raise RuntimeError("flaky pipeline")

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: always_fail)

    sleep_calls: list[float] = []
    monkeypatch.setattr(rl.time, "sleep", lambda duration: sleep_calls.append(duration))

    caplog.set_level("DEBUG", rl.logger.logger.name)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "demo"},
        critic_agent=None,
        retry_attempts=1,
        retry_backoff=0.25,
    )

    assert results == []
    assert attempt_counter["value"] == 2
    assert sleep_calls == pytest.approx([0.25])
    assert any(
        "Giving up after retries due to transient errors" in record.message
        for record in caplog.records
    )
