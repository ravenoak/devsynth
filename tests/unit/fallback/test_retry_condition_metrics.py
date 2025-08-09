from unittest.mock import Mock

import pytest

from devsynth import metrics
from devsynth.fallback import reset_prometheus_metrics, retry_with_exponential_backoff
from devsynth.metrics import retry_condition_counter


@pytest.mark.medium
def test_named_retry_condition_records_metrics_on_abort() -> None:
    """Named retry conditions record metrics when they fail."""
    metrics.reset_metrics()
    reset_prometheus_metrics()

    func = Mock(side_effect=Exception("boom"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_conditions={"needs_retry": "retry"},
        track_metrics=True,
    )(func)

    with pytest.raises(Exception):
        wrapped()

    assert func.call_count == 1
    assert metrics.get_retry_condition_metrics() == {"needs_retry": 1}
    assert retry_condition_counter.labels(condition="needs_retry")._value.get() == 1


@pytest.mark.medium
def test_named_retry_condition_allows_retry() -> None:
    """Successful named conditions do not increment metrics."""
    metrics.reset_metrics()
    reset_prometheus_metrics()

    func = Mock(side_effect=[Exception("please retry"), "ok"])
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_conditions={"needs_retry": "retry"},
        track_metrics=True,
    )(func)

    result = wrapped()

    assert result == "ok"
    assert func.call_count == 2
    assert metrics.get_retry_condition_metrics() == {}
