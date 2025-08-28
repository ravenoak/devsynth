import importlib
import time
from unittest.mock import MagicMock

import pytest

rl = importlib.import_module("devsynth.methodology.edrr.reasoning_loop")


def _slow_apply(team, task, critic, memory):
    # Simulate a tiny bit of work but not too much to slow the suite
    # This function should be called at most once when a strict time budget is set
    time.sleep(0.01)
    return {"status": "in_progress"}


@pytest.mark.fast
@pytest.mark.unit
def test_reasoning_loop_respects_total_time_budget(monkeypatch):
    """It stops when the total time budget is exhausted.

    ReqID: DR-6
    """

    monkeypatch.setattr(rl, "_apply_dialectical_reasoning", _slow_apply)

    # Set a very small budget so that after the first iteration and sleep,
    # the loop should decide to stop on the next check.
    results = rl.reasoning_loop(
        MagicMock(),
        {"solution": "initial"},
        MagicMock(),
        max_iterations=100,
        max_total_seconds=0.01,
    )

    # We expect at least one result, but far fewer than max_iterations
    assert 0 < len(results) < 5
