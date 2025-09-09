import time

import pytest

from devsynth.application.memory.circuit_breaker import CircuitBreaker


@pytest.mark.medium
def test_circuit_breaker_resets_after_timeout():
    """Circuit breaker transitions to CLOSED after timeout. ReqID: FR-60"""
    breaker = CircuitBreaker("demo", failure_threshold=1, reset_timeout=0.1)

    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        breaker.execute(boom)
    assert breaker.state.name == "OPEN"

    # Replace unbounded sleep with bounded polling to reduce flakiness per docs/plan.md §11
    deadline = time.time() + 0.5  # bounded wait up to 0.5s
    while time.time() < deadline and breaker.state.name != "HALF_OPEN":
        time.sleep(0.01)
    # Now the breaker should allow a trial execution
    assert breaker.execute(lambda: "ok") == "ok"
    assert breaker.state.name == "CLOSED"

    with pytest.raises(ValueError):
        breaker.execute(boom)
    assert breaker.state.name == "OPEN"
