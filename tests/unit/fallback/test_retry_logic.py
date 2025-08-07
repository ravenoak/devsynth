"""Tests for retry conditions and circuit breaker integration."""

from unittest.mock import Mock

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.fallback import (
    CircuitBreaker,
    circuit_breaker_state_counter,
    reset_prometheus_metrics,
    retry_with_exponential_backoff,
)


@pytest.mark.medium
def test_retry_conditions_respected_with_circuit_breaker() -> None:
    """Retry stops if conditions fail even when circuit breaker is present."""

    reset_prometheus_metrics()
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    func = Mock(side_effect=Exception("boom"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        jitter=False,
        retry_conditions=[lambda exc: "retry" in str(exc)],
        circuit_breaker=breaker,
    )(func)

    with pytest.raises(Exception):
        wrapped()

    assert func.call_count == 1
    assert (
        circuit_breaker_state_counter.labels(
            function="func", state=CircuitBreaker.OPEN
        )._value.get()
        == 0
    )


@pytest.mark.medium
def test_circuit_breaker_opens_and_records_metrics() -> None:
    """Circuit breaker transitions to OPEN and emits Prometheus metrics."""

    reset_prometheus_metrics()
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)

    func = Mock(side_effect=Exception("fail"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        jitter=False,
        circuit_breaker=breaker,
    )(func)

    with pytest.raises(DevSynthError) as err:
        wrapped()

    assert err.value.error_code == "CIRCUIT_OPEN"
    assert func.call_count == 2
    assert (
        circuit_breaker_state_counter.labels(
            function="func", state=CircuitBreaker.OPEN
        )._value.get()
        == 2
    )
