from __future__ import annotations

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl
from devsynth.exceptions import ConsensusError
from devsynth.methodology.edrr.contracts import CoordinatorRecorder, NullWSDETeam


@pytest.mark.fast
def test_reasoning_loop_retries_on_transient(monkeypatch):
    """Transient errors retry once before succeeding.

    ReqID: N/A"""

    calls = {"count": 0}

    def flaky(wsde, task, critic, memory):
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("temp")
        return {"status": "completed", "phase": "refine"}

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: flaky)
    monkeypatch.setattr(rl.time, "sleep", lambda s: None)

    out = rl.reasoning_loop(NullWSDETeam(), {}, None, retry_attempts=1)

    assert len(out) == 1
    assert calls["count"] == 2


@pytest.mark.fast
def test_reasoning_loop_retry_clamps_backoff_and_respects_budget(monkeypatch):
    """Exponential backoff honors the total budget by clamping sleep.

    ReqID: N/A"""

    call_count = {"value": 0}

    def transient_then_progress(wsde, task, critic, memory):
        call_count["value"] += 1
        if call_count["value"] < 3:
            raise RuntimeError("flaky")
        return {"status": "in_progress", "phase": "refine"}

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: transient_then_progress
    )

    clock = {"value": 0.0}
    sleep_calls: list[float] = []

    def fake_monotonic() -> float:
        return clock["value"]

    def fake_sleep(duration: float) -> None:
        sleep_calls.append(duration)
        clock["value"] += duration

    monkeypatch.setattr(rl.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(rl.time, "sleep", fake_sleep)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "x"},
        critic_agent=None,
        max_iterations=5,
        retry_attempts=2,
        retry_backoff=0.1,
        max_total_seconds=0.15,
    )

    assert call_count["value"] == 3  # two transient failures + success
    assert sleep_calls == pytest.approx([0.1, 0.05])
    assert results == [{"status": "in_progress", "phase": "refine"}]


@pytest.mark.fast
def test_reasoning_loop_logs_retry_exhaustion(monkeypatch, caplog):
    """Exhausting retries logs telemetry and returns no results."""

    def always_transient(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        rl, "_import_apply_dialectical_reasoning", lambda: always_transient
    )

    caplog.set_level("DEBUG", rl.logger.logger.name)

    results = rl.reasoning_loop(
        wsde_team=NullWSDETeam(),
        task={"problem": "telemetry"},
        critic_agent=None,
        retry_attempts=0,
    )

    assert results == []
    assert any(
        "Giving up after retries due to transient errors" in record.message
        for record in caplog.records
    )


@pytest.mark.fast
def test_reasoning_loop_records_consensus_failure_via_coordinator(monkeypatch):
    """ConsensusError stops the loop and notifies the coordinator.

    ReqID: N/A"""

    error = ConsensusError("no consensus")

    def always_fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: always_fail)

    coordinator = CoordinatorRecorder()

    results = rl.reasoning_loop(NullWSDETeam(), {}, None, coordinator=coordinator)

    assert results == []
    assert coordinator.failures == [error]
    assert coordinator.records == []


@pytest.mark.fast
def test_reasoning_loop_logs_consensus_failure_without_coordinator(monkeypatch, caplog):
    """ConsensusError without a coordinator is logged and stops the loop.

    ReqID: N/A"""

    def always_fail(*_args, **_kwargs):
        raise ConsensusError("disagreement")

    monkeypatch.setattr(rl, "_import_apply_dialectical_reasoning", lambda: always_fail)

    caplog.set_level("ERROR", rl.logger.logger.name)

    results = rl.reasoning_loop(NullWSDETeam(), {}, None)

    assert results == []
    assert any("Consensus failure" in record.message for record in caplog.records)
