import time

import pytest

from devsynth import metrics
from devsynth.fallback import (
    CircuitBreaker,
    reset_prometheus_metrics,
    retry_with_exponential_backoff,
)


@pytest.mark.fast
def test_named_condition_callbacks_record_metrics():
    reset_prometheus_metrics()
    calls = []

    def stop(exc: Exception, attempt: int) -> bool:  # pragma: no cover - simple
        calls.append(attempt)
        return False

    @retry_with_exponential_backoff(max_retries=1, condition_callbacks={"stop": stop})
    def boom() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        boom()

    assert calls == [0]
    metrics_dict = metrics.get_retry_condition_metrics()
    assert metrics_dict.get("stop:suppress") == 1


@pytest.mark.fast
def test_circuit_breaker_open_hook_and_metrics():
    reset_prometheus_metrics()
    events: list[str] = []

    cb = CircuitBreaker(
        failure_threshold=1,
        on_open=lambda name: events.append(f"open:{name}"),
    )

    @cb
    def flaky() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        flaky()

    assert events == ["open:flaky"]
    cb_metrics = metrics.get_circuit_breaker_state_metrics()
    assert cb_metrics["flaky:OPEN"] == 1
