"""Tests for retry conditions and circuit breaker integration."""

from unittest.mock import Mock

import pytest

from devsynth.exceptions import DevSynthError
from devsynth.fallback import (
    CircuitBreaker,
    circuit_breaker_state_counter,
    reset_prometheus_metrics,
    retry_stat_counter,
    retry_with_exponential_backoff,
    with_fallback,
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


@pytest.mark.medium
def test_retry_stat_prometheus_metrics_recorded() -> None:
    """Retry stat metrics are exposed via Prometheus counters."""

    reset_prometheus_metrics()

    func = Mock(side_effect=[Exception("boom"), "ok"])
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        jitter=False,
    )(func)

    assert wrapped() == "ok"
    assert (
        retry_stat_counter.labels(function="func", status="attempt")._value.get() == 1
    )
    assert (
        retry_stat_counter.labels(function="func", status="success")._value.get() == 1
    )


@pytest.mark.medium
def test_condition_callbacks_receive_typed_exception_and_attempt() -> None:
    """Condition callbacks receive typed arguments under the stricter contract."""

    reset_prometheus_metrics()

    class TypedError(Exception):
        pass

    observed: list[tuple[Exception, int]] = []

    def condition(exc: Exception, attempt: int) -> bool:
        observed.append((exc, attempt))
        assert isinstance(exc, TypedError)
        assert isinstance(attempt, int)
        return True

    func = Mock(side_effect=[TypedError("retry"), "ok"])
    func.__name__ = "typed_condition"

    wrapped = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        jitter=False,
        condition_callbacks={"typed": condition},
    )(func)

    assert wrapped() == "ok"
    assert len(observed) == 1
    exc, attempt = observed[0]
    assert isinstance(exc, TypedError)
    assert attempt == 0


@pytest.mark.medium
def test_with_fallback_conditions_and_circuit_breaker() -> None:
    """Fallback honors conditions and integrates with circuit breaker."""

    reset_prometheus_metrics()
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

    primary = Mock(side_effect=Exception("boom"))
    primary.__name__ = "primary"
    fallback = Mock(return_value="fallback")

    wrapped = with_fallback(
        fallback_function=fallback,
        fallback_conditions=[lambda exc: "retry" in str(exc)],
        circuit_breaker=breaker,
    )(primary)

    with pytest.raises(Exception):
        wrapped()

    assert fallback.call_count == 0
    assert (
        circuit_breaker_state_counter.labels(
            function="primary", state=CircuitBreaker.OPEN
        )._value.get()
        == 1
    )


@pytest.mark.medium
def test_error_map_respects_max_retries_with_circuit_breaker() -> None:
    """Error maps and circuit breaker cooperate while preserving typed callbacks."""

    reset_prometheus_metrics()

    class RetryableError(RuntimeError):
        pass

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

    attempts: list[int] = []

    def condition(exc: Exception, attempt: int) -> bool:
        attempts.append(attempt)
        assert isinstance(exc, RetryableError)
        return True

    func = Mock(side_effect=[RetryableError("retry")] * 3)
    func.__name__ = "typed_map"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        jitter=False,
        condition_callbacks={"typed": condition},
        error_retry_map={RetryableError: {"retry": True, "max_retries": 2}},
        circuit_breaker=breaker,
    )(func)

    with pytest.raises(RetryableError):
        wrapped()

    assert attempts == [0, 1, 2]
    assert func.call_count == 3
    assert breaker.state == CircuitBreaker.OPEN
    assert (
        circuit_breaker_state_counter.labels(
            function="typed_map", state=CircuitBreaker.OPEN
        )._value.get()
        >= 1
    )
