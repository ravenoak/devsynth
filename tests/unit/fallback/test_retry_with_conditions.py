from unittest.mock import Mock

import pytest

from devsynth import metrics
from devsynth.fallback import reset_prometheus_metrics, retry_with_exponential_backoff


@pytest.mark.medium
def test_error_policy_overrides_max_retries() -> None:
    """Per-error policies override global max retries."""
    metrics.reset_metrics()
    reset_prometheus_metrics()

    func = Mock(side_effect=[ValueError("bad"), ValueError("bad"), "ok"])
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        track_metrics=True,
        error_retry_map={ValueError: {"max_retries": 1}},
    )(func)

    with pytest.raises(ValueError):
        wrapped()

    assert func.call_count == 2
    assert metrics.get_retry_metrics()["failure"] == 1


@pytest.mark.medium
def test_error_policy_prevents_retry() -> None:
    """Per-error policies can disable retries entirely."""
    metrics.reset_metrics()
    reset_prometheus_metrics()

    func = Mock(side_effect=KeyError("nope"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=5,
        initial_delay=0,
        track_metrics=True,
        error_retry_map={KeyError: {"retry": False}},
    )(func)

    with pytest.raises(KeyError):
        wrapped()

    assert func.call_count == 1
    assert metrics.get_retry_metrics()["abort"] == 1


@pytest.mark.medium
def test_condition_metrics_track_trigger_and_suppress() -> None:
    """Condition metrics increment on trigger and suppress."""
    metrics.reset_metrics()
    reset_prometheus_metrics()

    func = Mock(side_effect=[Exception("please retry"), Exception("boom")])
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=1,
        initial_delay=0,
        retry_conditions={"needs_retry": "retry"},
        track_metrics=True,
    )(func)

    with pytest.raises(Exception):
        wrapped()

    condition_stats = metrics.get_retry_condition_metrics()
    assert condition_stats["needs_retry:trigger"] == 1
    assert condition_stats["needs_retry:suppress"] == 1
