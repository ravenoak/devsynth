import pytest

from devsynth.exceptions import DevSynthError
from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff
from devsynth.metrics import (
    get_circuit_breaker_state_metrics,
    get_retry_condition_metrics,
    get_retry_stat_metrics,
    reset_metrics,
)

pytestmark = [pytest.mark.fast]


def test_named_retry_condition_aborts_and_records_metrics():
    """Ensure named retry conditions abort execution and update metrics."""
    reset_metrics()

    def always_fail() -> None:
        raise RuntimeError("boom")

    decorated = retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=0,
        jitter=False,
        retry_conditions={"always_false": lambda exc: False},
    )(always_fail)

    with pytest.raises(RuntimeError):
        decorated()

    stats = get_retry_stat_metrics()
    condition_stats = get_retry_condition_metrics()
    assert stats["always_fail:abort"] == 1
    assert condition_stats["always_false:suppress"] == 1


def test_circuit_breaker_open_records_abort_metrics():
    """Circuit breaker should record abort metrics when open."""
    reset_metrics()

    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout=100,
        exception_types=(ValueError,),
    )

    def fail() -> None:
        raise ValueError("fail")

    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        jitter=False,
        circuit_breaker=breaker,
        retryable_exceptions=(ValueError,),
    )(fail)

    with pytest.raises(DevSynthError):
        decorated()

    stats = get_retry_stat_metrics()
    cb_stats = get_circuit_breaker_state_metrics()
    assert stats["fail:abort"] == 1
    assert cb_stats["fail:OPEN"] >= 1
