import time
import pytest

from devsynth.application.memory.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
)


def test_circuit_breaker_opens_after_failures():
    breaker = CircuitBreaker("demo", failure_threshold=2, reset_timeout=1.0)

    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        breaker.execute(boom)
    with pytest.raises(ValueError):
        breaker.execute(boom)

    assert breaker.state.name == "OPEN"
    with pytest.raises(CircuitBreakerOpenError):
        breaker.execute(lambda: "ok")


def test_registry_returns_same_instance():
    registry = CircuitBreakerRegistry()
    a = registry.get_or_create("alpha", failure_threshold=1, reset_timeout=1)
    b = registry.get_or_create("alpha")
    assert a is b
