from unittest.mock import Mock

import pytest

from devsynth.fallback import (
    FallbackHandler,
    reset_prometheus_metrics,
    retry_condition_counter,
    retry_with_exponential_backoff,
)
from devsynth.metrics import (
    get_retry_condition_metrics,
    get_retry_error_metrics,
    get_retry_metrics,
    reset_metrics,
)


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
    reset_prometheus_metrics()
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
    cond_metrics = get_retry_condition_metrics()
    assert metrics.get("abort") == 1
    assert err_metrics.get("ValueError") == 1
    assert cond_metrics.get("policy:ValueError:suppress") == 1
    assert (
        retry_condition_counter.labels(
            condition="policy:ValueError:suppress"
        )._value.get()
        == 1
    )


@pytest.mark.medium
def test_retry_error_map_matches_subclass():
    reset_metrics()
    reset_prometheus_metrics()
    mock_func = Mock(side_effect=ValueError("boom"))
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=0,
        track_metrics=True,
        error_retry_map={Exception: {"max_retries": 1}},
    )(mock_func)
    with pytest.raises(ValueError):
        decorated()
    metrics = get_retry_metrics()
    cond_metrics = get_retry_condition_metrics()
    assert mock_func.call_count == 2
    assert metrics.get("attempt") == 1
    assert cond_metrics.get("policy:Exception:trigger") == 2
    assert (
        retry_condition_counter.labels(
            condition="policy:Exception:trigger"
        )._value.get()
        == 2
    )


@pytest.mark.medium
def test_fallback_handler_predicate_metrics() -> None:
    """FallbackHandler records metrics for predicate-triggered fallbacks."""
    reset_metrics()
    reset_prometheus_metrics()

    class Response:
        def __init__(self, status_code: int) -> None:
            self.status_code = status_code

    responses = [Response(503), Response(200)]
    primary = Mock(side_effect=lambda: responses.pop(0))
    primary.__name__ = "primary"
    fallback = Mock(side_effect=lambda: responses.pop(0))

    wrapped = FallbackHandler(
        fallback_function=fallback,
        retry_predicates={"server_error": lambda r: r.status_code >= 500},
        track_metrics=True,
    )(primary)

    result = wrapped()

    assert result.status_code == 200
    metrics = get_retry_metrics()
    cond_metrics = get_retry_condition_metrics()
    assert metrics.get("predicate") == 1
    assert metrics.get("success") == 1
    assert cond_metrics.get("predicate:server_error:trigger") == 1
    assert cond_metrics.get("predicate:server_error:suppress") == 1
