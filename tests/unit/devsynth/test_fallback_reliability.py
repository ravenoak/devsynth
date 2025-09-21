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
def test_retry_with_exponential_backoff_records_metrics() -> None:
    """ReqID: RETRY-01; Issue: issues/Enhance-retry-mechanism.md"""

    reset_prometheus_metrics()
    attempts = {"count": 0}

    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=0,
        max_delay=0,
        jitter=False,
    )
    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient error")
        return "ok"

    assert flaky() == "ok"
    assert attempts["count"] == 3

    assert metrics.get_retry_metrics() == {"attempt": 2, "success": 1}
    assert metrics.get_retry_count_metrics() == {"flaky": 2}
    assert metrics.get_retry_error_metrics() == {"RuntimeError": 2}
    assert metrics.get_retry_stat_metrics() == {
        "flaky:attempt": 2,
        "flaky:success": 1,
    }


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
