"""Regression tests for retry logic with circuit breaker and condition hooks."""

from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from devsynth.application.memory.circuit_breaker import CircuitBreakerOpenError
from devsynth.application.memory.retry import (
    ConditionCallback,
    _CounterWrapper,
    reset_memory_retry_metrics,
    retry_error_counter,
    retry_event_counter,
    retry_with_backoff,
)


def _counter_value(counter: _CounterWrapper) -> float:
    """Return the numeric value from a wrapped Prometheus counter."""

    return cast(float, cast(Any, counter._counter)._value.get())


class TestRetryLogic:
    """Tests for retry integration features."""

    def setup_method(self) -> None:
        """Reset metrics before each test."""
        reset_memory_retry_metrics()

    @pytest.mark.medium
    def test_condition_callback_aborts_retry(self) -> None:
        """Ensure condition callbacks can abort further retries."""

        mock_func = MagicMock(side_effect=ValueError("fail"))

        def condition_cb(exc: Exception, count: int) -> bool:
            return False

        decorated = retry_with_backoff(
            max_retries=3,
            initial_backoff=0.01,
            backoff_multiplier=1.0,
            jitter=False,
            condition_callbacks=[cast(ConditionCallback, condition_cb)],
        )(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert mock_func.call_count == 1
        abort_counter = cast(
            _CounterWrapper, retry_event_counter.labels(status="abort")
        )
        abort_error = cast(
            _CounterWrapper,
            retry_error_counter.labels(error_type="ValueError"),
        )
        assert _counter_value(abort_counter) == 1
        assert _counter_value(abort_error) == 1

    @pytest.mark.medium
    def test_condition_callback_receives_typed_arguments(self) -> None:
        """Condition callbacks expose typed exception payloads and attempt counts."""

        mock_func = MagicMock(side_effect=ValueError("fail"))
        captured: list[tuple[Exception, int]] = []

        def condition_cb(exc: Exception, count: int) -> bool:
            captured.append((exc, count))
            return False

        decorated = retry_with_backoff(
            max_retries=3,
            initial_backoff=0.01,
            backoff_multiplier=1.0,
            jitter=False,
            condition_callbacks=[cast(ConditionCallback, condition_cb)],
        )(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert len(captured) == 1
        exc, attempt = captured[0]
        assert isinstance(exc, ValueError)
        assert attempt == 0

        assert mock_func.call_count == 1
        abort_counter = cast(
            _CounterWrapper, retry_event_counter.labels(status="abort")
        )
        abort_error = cast(
            _CounterWrapper,
            retry_error_counter.labels(error_type="ValueError"),
        )
        assert _counter_value(abort_counter) == 1
        assert _counter_value(abort_error) == 1

    @pytest.mark.medium
    def test_circuit_breaker_stops_retries(self) -> None:
        """Verify circuit breaker prevents retries once open."""

        mock_func = MagicMock(side_effect=ValueError("boom"))
        decorated = retry_with_backoff(
            max_retries=5,
            initial_backoff=0.01,
            backoff_multiplier=1.0,
            jitter=False,
            circuit_breaker_name="retry_test_cb",
            circuit_breaker_failure_threshold=2,
            circuit_breaker_reset_timeout=1.0,
        )(mock_func)

        with pytest.raises(CircuitBreakerOpenError):
            decorated()

        assert mock_func.call_count == 2
        attempt_counter = cast(
            _CounterWrapper, retry_event_counter.labels(status="attempt")
        )
        error_counter = cast(
            _CounterWrapper,
            retry_error_counter.labels(error_type="ValueError"),
        )
        abort_counter = cast(
            _CounterWrapper, retry_event_counter.labels(status="abort")
        )
        assert _counter_value(attempt_counter) == 2
        assert _counter_value(error_counter) == 2
        assert _counter_value(abort_counter) == 1
