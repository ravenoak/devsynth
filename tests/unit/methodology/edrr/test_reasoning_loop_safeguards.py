"""Deterministic recursion safeguard tests for the reasoning loop."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

import pytest

from devsynth.methodology.edrr.contracts import NullWSDETeam
from devsynth.methodology.edrr.reasoning_loop import Phase

rl = importlib.import_module("devsynth.methodology.edrr.reasoning_loop")


class _RecorderCoordinator:
    """Coordinator capturing the order of recorded phases."""

    def __init__(self) -> None:
        self.recorded: list[Phase] = []

    def record_expand_results(self, result: dict[str, Any]) -> dict[str, Any]:
        self.recorded.append(Phase.EXPAND)
        return result

    def record_differentiate_results(self, result: dict[str, Any]) -> dict[str, Any]:
        self.recorded.append(Phase.DIFFERENTIATE)
        return result

    def record_refine_results(self, result: dict[str, Any]) -> dict[str, Any]:
        self.recorded.append(Phase.REFINE)
        return result

    def record_consensus_failure(
        self, _exc: Exception
    ) -> None:  # pragma: no cover - defensive
        return None


def patch_reasoning_loop(
    monkeypatch: pytest.MonkeyPatch,
    fake_callable: Callable[[Any, dict[str, Any], Any, Any], dict[str, Any]],
) -> None:
    """Patch reasoning loop internals to use deterministic callables."""

    monkeypatch.setattr(
        rl, "_apply_dialectical_reasoning", fake_callable, raising=False
    )
    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: fake_callable
    )


@pytest.mark.fast
def test_invalid_next_phase_falls_back_to_transition_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown ``next_phase`` values fall back to deterministic transitions."""

    coordinator = _RecorderCoordinator()
    calls = {"count": 0}

    def fake_apply(_: Any, __: dict[str, Any], ___: Any, ____: Any) -> dict[str, Any]:
        calls["count"] += 1
        if calls["count"] < 3:
            return {"status": "in_progress", "next_phase": "mystery"}
        return {"status": "completed", "phase": "refine"}

    patch_reasoning_loop(monkeypatch, fake_apply)
    monkeypatch.setattr(rl.time, "sleep", lambda _seconds: None)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"solution": "seed"},
        critic_agent=None,
        coordinator=coordinator,
        phase=Phase.EXPAND,
        max_iterations=5,
    )

    assert len(results) == 3
    assert [phase.value for phase in coordinator.recorded] == [
        Phase.EXPAND.value,
        Phase.DIFFERENTIATE.value,
        Phase.REFINE.value,
    ]


@pytest.mark.fast
def test_missing_status_relies_on_max_iterations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Results without a ``status`` key terminate via the iteration safeguard."""

    calls = {"count": 0}

    def fake_apply(_: Any, task: dict[str, Any], __: Any, ___: Any) -> dict[str, Any]:
        calls["count"] += 1
        return {"phase": task.get("phase", "refine")}

    patch_reasoning_loop(monkeypatch, fake_apply)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"solution": "seed"},
        critic_agent=None,
        max_iterations=2,
    )

    assert len(results) == 2
    assert calls["count"] == 2


@pytest.mark.fast
def test_reasoning_loop_raises_for_non_mapping_results(monkeypatch):
    """Returning a non-mapping payload triggers a TypeError guard."""

    def invalid_apply(*_args, **_kwargs):
        return "unsupported"

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: invalid_apply
    )

    with pytest.raises(TypeError, match="must return a mapping payload"):
        rl.reasoning_loop(NullWSDETeam(), {"solution": "seed"}, None)


@pytest.mark.fast
def test_reasoning_loop_rejects_non_mapping_task_payload() -> None:
    """Invalid task inputs surface the ensure_dialectical_task TypeError."""

    with pytest.raises(TypeError, match="Unsupported task payload type"):
        rl.reasoning_loop(NullWSDETeam(), "not-a-task", None)
