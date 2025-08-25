import types

import pytest

import devsynth.methodology.edrr.reasoning_loop as rl


class DummyTeam:
    pass


class DummyCritic:
    pass


@pytest.mark.unit
def test_reasoning_loop_retries_on_transient_error(monkeypatch):
    calls = {"count": 0}

    def flaky_apply(team, task, critic, memory):  # signature mirrors underlying call
        calls["count"] += 1
        # First call fails with a transient error; second returns success
        if calls["count"] == 1:
            raise RuntimeError("transient")
        return {
            "status": "completed",
            "phase": "refine",
            "synthesis": task.get("solution"),
        }

    # Patch the internal alias used by the reasoning loop
    monkeypatch.setattr(
        "devsynth.methodology.edrr.reasoning_loop._apply_dialectical_reasoning",
        flaky_apply,
        raising=True,
    )

    team = DummyTeam()
    critic = DummyCritic()
    task = {"solution": "draft"}

    results = rl.reasoning_loop(
        team,
        task,
        critic,
        memory_integration=None,
        phase=rl.Phase.REFINE,
        max_iterations=1,
        retry_attempts=1,
        retry_backoff=0.0,  # no waiting in tests
        coordinator=None,
    )

    assert len(results) == 1
    assert results[-1]["status"] == "completed"
    assert calls["count"] == 2, "Should retry once after transient error"
