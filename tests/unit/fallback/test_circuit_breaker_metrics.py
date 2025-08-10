from unittest.mock import Mock

import pytest

from devsynth import metrics
from devsynth.exceptions import DevSynthError
from devsynth.fallback import CircuitBreaker, retry_with_exponential_backoff


@pytest.mark.medium
def test_circuit_breaker_state_metrics() -> None:
    """Circuit breaker state transitions are tracked in metrics module."""

    metrics.reset_metrics()
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)

    func = Mock(side_effect=Exception("boom"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=1, initial_delay=0, jitter=False, circuit_breaker=breaker
    )(func)

    with pytest.raises(DevSynthError) as err:
        wrapped()

    assert err.value.error_code == "CIRCUIT_OPEN"
    assert func.call_count == 1
    assert metrics.get_circuit_breaker_state_metrics() == {"func:OPEN": 2}
