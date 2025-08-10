from unittest.mock import Mock

import pytest

from devsynth.application.memory import retry as memory_retry
from devsynth.fallback import (
    reset_prometheus_metrics,
    retry_event_counter,
    retry_with_exponential_backoff,
)

retry_with_backoff = memory_retry.retry_with_backoff
memory_retry_event_counter = memory_retry.retry_event_counter
reset_memory_retry_metrics = memory_retry.reset_memory_retry_metrics


@pytest.mark.medium
def test_condition_callback_prevents_retry():
    called = False

    def callback(exc: Exception, attempt: int) -> bool:
        nonlocal called
        called = True
        return False

    func = Mock(side_effect=Exception("boom"))
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=2, initial_delay=0, condition_callbacks=[callback]
    )(func)

    with pytest.raises(Exception):
        wrapped()

    assert called is True
    assert func.call_count == 1


@pytest.mark.medium
def test_prometheus_metrics_recorded():
    reset_prometheus_metrics()
    func = Mock(side_effect=[Exception("err"), "ok"])
    func.__name__ = "func"

    wrapped = retry_with_exponential_backoff(
        max_retries=2, initial_delay=0, track_metrics=True
    )(func)

    result = wrapped()

    assert result == "ok"
    assert retry_event_counter.labels(status="attempt")._value.get() == 1
    assert retry_event_counter.labels(status="success")._value.get() == 1


@pytest.mark.medium
def test_memory_retry_metrics_and_callback():
    reset_memory_retry_metrics()
    cb_called = False

    def cond_cb(exc: Exception, attempt: int) -> bool:
        nonlocal cb_called
        cb_called = True
        return True

    func = Mock(side_effect=[Exception("err"), "ok"])
    func.__name__ = "mem_func"

    wrapped = retry_with_backoff(
        max_retries=2,
        initial_backoff=0,
        condition_callbacks=[cond_cb],
    )(func)

    result = wrapped()

    assert result == "ok"
    assert cb_called is True
    assert memory_retry_event_counter.labels(status="attempt")._value.get() == 1
    assert memory_retry_event_counter.labels(status="success")._value.get() == 1
