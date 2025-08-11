from unittest.mock import Mock

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.fallback import (
    ANONYMOUS_CONDITION,
    CircuitBreaker,
    circuit_breaker_state_counter,
    reset_prometheus_metrics,
    retry_with_exponential_backoff,
)
from devsynth.metrics import (
    get_circuit_breaker_state_metrics,
    get_retry_condition_metrics,
    get_retry_metrics,
    reset_metrics,
)


@pytest.mark.medium
def test_anonymous_retry_condition_records_metrics() -> None:
    """Anonymous retry conditions emit condition and retry metrics."""
    reset_metrics()
    reset_prometheus_metrics()

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
    func = Mock(side_effect=Exception("boom"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        jitter=False,
        retry_conditions=[lambda exc: False],
        circuit_breaker=breaker,
        track_metrics=True,
    )(func)

    with pytest.raises(Exception):
        wrapped()

    assert func.call_count == 1

    retry_metrics = get_retry_metrics()
    assert retry_metrics.get("abort") == 1

    condition_metrics = get_retry_condition_metrics()
    assert condition_metrics.get(ANONYMOUS_CONDITION) == 1
    assert (
        circuit_breaker_state_counter.labels(
            function="func", state=CircuitBreaker.OPEN
        )._value.get()
        == 0
    )
    assert get_circuit_breaker_state_metrics() == {}


@pytest.mark.medium
def test_circuit_breaker_open_emits_metrics() -> None:
    """Circuit breaker transitions to OPEN and emits metrics."""
    reset_metrics()
    reset_prometheus_metrics()

    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
    func = Mock(side_effect=Exception("fail"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        jitter=False,
        circuit_breaker=breaker,
        track_metrics=True,
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
    metrics = get_circuit_breaker_state_metrics()
    assert metrics.get("func:OPEN") == 2
    retry_metrics = get_retry_metrics()
    assert retry_metrics.get("abort") == 1
