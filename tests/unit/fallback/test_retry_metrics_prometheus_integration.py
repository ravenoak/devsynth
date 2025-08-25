from unittest.mock import Mock

import pytest

from devsynth import metrics
from devsynth.fallback import (
    reset_prometheus_metrics,
)
from devsynth.fallback import retry_event_counter as fallback_retry_event_counter
from devsynth.fallback import (
    retry_with_exponential_backoff,
)
from devsynth.metrics import retry_event_counter as metrics_retry_event_counter


@pytest.mark.medium
def test_retry_metrics_synced_with_prometheus() -> None:
    """Retry decorator updates both in-memory and Prometheus counters."""

    metrics.reset_metrics()
    reset_prometheus_metrics()

    func = Mock(side_effect=[Exception("err"), "ok"])
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=2, initial_delay=0, track_metrics=True
    )(func)

    result = wrapped()

    assert result == "ok"

    # In-memory counters via metrics module
    assert metrics.get_retry_metrics() == {"attempt": 1, "success": 1}

    # Prometheus counters in fallback.py
    assert fallback_retry_event_counter.labels(status="attempt")._value.get() == 1
    assert fallback_retry_event_counter.labels(status="success")._value.get() == 1

    # Prometheus counters exposed by metrics module
    assert metrics_retry_event_counter.labels(status="attempt")._value.get() == 1
    assert metrics_retry_event_counter.labels(status="success")._value.get() == 1
