import pytest
from unittest.mock import Mock

from devsynth.fallback import retry_with_exponential_backoff
from devsynth.metrics import get_retry_metrics, reset_metrics, get_retry_error_metrics


@pytest.mark.medium
def test_retry_metrics_success():
    reset_metrics()
    mock_func = Mock(side_effect=[Exception("err"), "ok"])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2, initial_delay=0, track_metrics=True
    )(mock_func)
    result = decorated()
    assert result == "ok"
    metrics = get_retry_metrics()
    assert metrics.get("attempt") == 1
    assert metrics.get("success") == 1


@pytest.mark.medium
def test_retry_metrics_failure():
    reset_metrics()
    mock_func = Mock(side_effect=Exception("err"))
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=1, initial_delay=0, track_metrics=True
    )(mock_func)
    with pytest.raises(Exception):
        decorated()
    metrics = get_retry_metrics()
    # one retry attempt, failure recorded
    assert metrics.get("attempt") == 1
    assert metrics.get("failure") == 1


@pytest.mark.medium
def test_retry_metrics_abort_when_not_retryable():
    reset_metrics()
    mock_func = Mock(side_effect=Exception("err"))
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        should_retry=lambda exc: False,
        track_metrics=True,
    )(mock_func)
    with pytest.raises(Exception):
        decorated()
    metrics = get_retry_metrics()
    assert metrics.get("abort") == 1


@pytest.mark.medium
def test_retry_metrics_invalid_result():
    reset_metrics()
    mock_func = Mock(side_effect=["bad", "good"])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_on_result=lambda r: r == "bad",
        track_metrics=True,
    )(mock_func)
    result = decorated()
    metrics = get_retry_metrics()
    assert result == "good"
    assert metrics.get("invalid") == 1


@pytest.mark.medium
def test_retry_metrics_success_without_retries():
    reset_metrics()
    mock_func = Mock(return_value="ok")
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=1, initial_delay=0, track_metrics=True
    )(mock_func)
    result = decorated()
    metrics = get_retry_metrics()
    assert result == "ok"
    assert metrics.get("success") == 1
    assert metrics.get("attempt") is None


@pytest.mark.medium
def test_retry_error_metrics():
    reset_metrics()
    mock_func = Mock(side_effect=[ValueError("bad"), "ok"])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2, initial_delay=0, track_metrics=True
    )(mock_func)
    result = decorated()
    metrics = get_retry_error_metrics()
    assert result == "ok"
    assert metrics.get("ValueError") == 1


@pytest.mark.medium
def test_retry_error_map_prevents_retry():
    reset_metrics()
    mock_func = Mock(side_effect=ValueError("boom"))
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        track_metrics=True,
        error_retry_map={ValueError: False},
    )(mock_func)
    with pytest.raises(ValueError):
        decorated()
    metrics = get_retry_metrics()
    err_metrics = get_retry_error_metrics()
    assert metrics.get("abort") == 1
    assert err_metrics.get("ValueError") == 1
