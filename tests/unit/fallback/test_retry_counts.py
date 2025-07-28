import pytest
from unittest.mock import Mock

from devsynth.fallback import retry_with_exponential_backoff
from devsynth.metrics import (
    get_retry_metrics,
    get_retry_count_metrics,
    reset_metrics,
)


class NetworkError(Exception):
    pass


def test_retry_count_metrics():
    reset_metrics()
    mock_func = Mock(side_effect=[Exception("err"), Exception("err"), "ok"])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=3, initial_delay=0, track_metrics=True
    )(mock_func)

    result = decorated()

    assert result == "ok"
    metrics = get_retry_count_metrics()
    assert metrics.get("mock_func") == 2
    retry_metrics = get_retry_metrics()
    assert retry_metrics.get("attempt") == 2
    assert retry_metrics.get("success") == 1


def test_retry_only_network_errors():
    reset_metrics()
    mock_func = Mock(side_effect=[NetworkError("net"), ValueError("boom")])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=0,
        retryable_exceptions=(NetworkError,),
        track_metrics=True,
    )(mock_func)

    with pytest.raises(ValueError):
        decorated()

    metrics = get_retry_count_metrics()
    assert metrics.get("mock_func") == 1
    retry_metrics = get_retry_metrics()
    assert retry_metrics.get("attempt") == 1
