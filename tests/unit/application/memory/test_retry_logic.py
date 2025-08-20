"""Regression tests for retry logic with circuit breaker and condition hooks."""

from unittest.mock import MagicMock

import pytest

from devsynth.application.memory.circuit_breaker import CircuitBreakerOpenError
from devsynth.application.memory.retry import (
    reset_memory_retry_metrics,
    retry_error_counter,
    retry_event_counter,
    retry_with_backoff,
)


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
            condition_callbacks=[condition_cb],
        )(mock_func)

        with pytest.raises(ValueError):
            decorated()

        assert mock_func.call_count == 1
        assert retry_event_counter.labels(status="abort")._value.get() == 1
        assert retry_error_counter.labels(error_type="ValueError")._value.get() == 1

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
        assert retry_event_counter.labels(status="attempt")._value.get() == 2
        assert retry_error_counter.labels(error_type="ValueError")._value.get() == 2
        assert retry_event_counter.labels(status="abort")._value.get() == 1
