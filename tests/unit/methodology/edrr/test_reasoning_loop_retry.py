import importlib

import pytest

rl = importlib.import_module("devsynth.methodology.edrr.reasoning_loop")


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

    monkeypatch.setattr(rl, "_apply_dialectical_reasoning", flaky)
    monkeypatch.setattr(rl.time, "sleep", lambda s: None)
    out = rl.reasoning_loop(None, {}, None, retry_attempts=1)
    assert len(out) == 1
    assert calls["count"] == 2
