import time
import pytest

from devsynth.application.memory.circuit_breaker import CircuitBreaker


def test_circuit_breaker_resets_after_timeout():
    breaker = CircuitBreaker("demo", failure_threshold=1, reset_timeout=0.1)

    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        breaker.execute(boom)
    assert breaker.state.name == "OPEN"

    time.sleep(0.11)
    assert breaker.execute(lambda: "ok") == "ok"
    assert breaker.state.name == "CLOSED"

    with pytest.raises(ValueError):
        breaker.execute(boom)
    assert breaker.state.name == "OPEN"
