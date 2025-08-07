from unittest.mock import Mock

import pytest

from devsynth.fallback import (
    retry_with_exponential_backoff,
    retry_event_counter,
    reset_prometheus_metrics,
)
import importlib.util
import pathlib
import sys

_memory_retry_path = pathlib.Path(__file__).resolve().parents[3] / "src/devsynth/application/memory/retry.py"
spec = importlib.util.spec_from_file_location(
    "memory_retry", _memory_retry_path
)
memory_retry = importlib.util.module_from_spec(spec)
sys.modules["memory_retry"] = memory_retry
assert spec.loader is not None
spec.loader.exec_module(memory_retry)

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
    assert (
        retry_event_counter.labels(status="attempt")._value.get() == 1
    )
    assert (
        retry_event_counter.labels(status="success")._value.get() == 1
    )


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
    assert (
        memory_retry_event_counter.labels(status="attempt")._value.get() == 1
    )
    assert (
        memory_retry_event_counter.labels(status="success")._value.get() == 1
    )
