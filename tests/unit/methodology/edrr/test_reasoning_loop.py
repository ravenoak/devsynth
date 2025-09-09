import pytest

from devsynth.methodology.edrr.reasoning_loop import Phase, reasoning_loop


@pytest.mark.fast
def test_reasoning_loop_completes_with_deterministic_seed(monkeypatch):
    calls = {"count": 0}

    def fake_apply(wsde_team, task, critic_agent, memory_integration):
        calls["count"] += 1
        # Simulate progress then completion with phase info
        if calls["count"] == 1:
            return {
                "status": "in_progress",
                "synthesis": "partial",
                "phase": "expand",
                "next_phase": "differentiate",
            }
        return {
            "status": "completed",
            "synthesis": "final",
            "phase": "refine",
        }

    # Patch the internal function used by reasoning_loop
    import devsynth.methodology.edrr.reasoning_loop as rl

    monkeypatch.setattr(rl, "_apply_dialectical_reasoning", fake_apply)

    out = reasoning_loop(
        wsde_team=None,
        task={"problem": "X"},
        critic_agent=None,
        memory_integration=None,
        phase=Phase.REFINE,
        max_iterations=5,
        deterministic_seed=123,
        max_total_seconds=1.0,
    )

    assert len(out) == 2
    assert out[-1]["status"] == "completed"
    # Ensure synthesis propagated
    assert out[0]["synthesis"] == "partial"
    assert out[1]["synthesis"] == "final"
