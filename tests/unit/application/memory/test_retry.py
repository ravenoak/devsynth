"""
Unit tests for the retry mechanism with exponential backoff.
"""

import time
from unittest.mock import MagicMock, call, patch

import pytest

from devsynth.application.memory.dto import MemoryRecord
from devsynth.application.memory.retry import (
    DEFAULT_RETRY_CONFIG,
    NETWORK_RETRY_CONFIG,
    PERSISTENT_RETRY_CONFIG,
    QUICK_RETRY_CONFIG,
    RetryConfig,
    RetryError,
    retry_memory_operation,
    retry_operation,
    retry_with_backoff,
    with_retry,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType


class TestRetryWithBackoff:
    """Tests for the retry_with_backoff decorator."""

    @pytest.mark.medium
    def test_retry_with_backoff_successful_execution(self):
        """Test that the decorator returns the result when the function succeeds."""

        @retry_with_backoff(max_retries=3)
        def decorated_func(arg1, arg2=None):
            return f"{arg1}-{arg2}"

        result = decorated_func("value1", arg2="value2")
        assert result == "value1-value2"

    @pytest.mark.medium
    def test_retry_with_backoff_retry_on_failure(self):
        """Test that the decorator retries when the function fails."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            ValueError("first failure"),
            ValueError("second failure"),
            "success",
        ]
        decorated_func = retry_with_backoff(
            max_retries=3, initial_backoff=0.01, backoff_multiplier=1.0
        )(mock_func)
        result = decorated_func()
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.medium
    def test_retry_with_backoff_max_retries_exceeded(self):
        """Test that the decorator raises RetryError when max retries is exceeded."""
        mock_func = MagicMock(side_effect=ValueError("test error"))
        decorated_func = retry_with_backoff(
            max_retries=2, initial_backoff=0.01, backoff_multiplier=1.0
        )(mock_func)
        with pytest.raises(RetryError) as excinfo:
            decorated_func()
        assert "All 2 retry attempts failed" in str(excinfo.value)
        assert mock_func.call_count == 3

    @pytest.mark.medium
    def test_retry_with_backoff_exceptions_to_retry(self):
        """Test that the decorator only retries specified exceptions."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            ValueError("retry this"),
            TypeError("don't retry this"),
            "success",
        ]
        decorated_func = retry_with_backoff(
            max_retries=3, initial_backoff=0.01, exceptions_to_retry=[ValueError]
        )(mock_func)
        with pytest.raises(TypeError, match="don't retry this"):
            decorated_func()
        assert mock_func.call_count == 2

    @pytest.mark.medium
    def test_retry_with_backoff_backoff_calculation(self):
        """Test that the backoff time increases exponentially."""
        with patch("time.sleep") as mock_sleep:
            mock_func = MagicMock(side_effect=ValueError("test error"))
            decorated_func = retry_with_backoff(
                max_retries=3, initial_backoff=1.0, backoff_multiplier=2.0, jitter=False
            )(mock_func)
            with pytest.raises(RetryError):
                decorated_func()
            assert mock_sleep.call_count == 3
            assert mock_sleep.call_args_list[0][0][0] == 1.0
            assert mock_sleep.call_args_list[1][0][0] == 2.0
            assert mock_sleep.call_args_list[2][0][0] == 4.0

    @pytest.mark.medium
    def test_retry_with_backoff_max_backoff(self):
        """Test that the backoff time is capped at max_backoff."""
        with patch("time.sleep") as mock_sleep:
            mock_func = MagicMock(side_effect=ValueError("test error"))
            decorated_func = retry_with_backoff(
                max_retries=3,
                initial_backoff=2.0,
                backoff_multiplier=3.0,
                max_backoff=5.0,
                jitter=False,
            )(mock_func)
            with pytest.raises(RetryError):
                decorated_func()
            assert mock_sleep.call_count == 3
            assert mock_sleep.call_args_list[0][0][0] == 2.0
            assert mock_sleep.call_args_list[1][0][0] == 5.0
            assert mock_sleep.call_args_list[2][0][0] == 5.0


class TestRetryOperation:
    """Tests for the retry_operation function."""

    @pytest.mark.medium
    def test_retry_operation_successful_execution(self):
        """Test that retry_operation returns the result when the function succeeds."""

        def decorated_func(arg1, arg2=None):
            return f"{arg1}-{arg2}"

        result = retry_operation(
            decorated_func,
            max_retries=3,
            initial_backoff=0.01,
            arg1="value1",
            arg2="value2",
        )
        assert result == "value1-value2"

    @pytest.mark.medium
    def test_retry_operation_retry_on_failure(self):
        """Test that retry_operation retries when the function fails."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            ValueError("first failure"),
            ValueError("second failure"),
            "success",
        ]
        result = retry_operation(
            mock_func, max_retries=3, initial_backoff=0.01, backoff_multiplier=1.0
        )
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.medium
    def test_retry_operation_max_retries_exceeded(self):
        """Test that retry_operation raises RetryError when max retries is exceeded."""
        mock_func = MagicMock(side_effect=ValueError("test error"))
        with pytest.raises(RetryError) as excinfo:
            retry_operation(
                mock_func, max_retries=2, initial_backoff=0.01, backoff_multiplier=1.0
            )
        assert "All 2 retry attempts failed" in str(excinfo.value)
        assert mock_func.call_count == 3


class TestRetryConfig:
    """Tests for the RetryConfig class and predefined configurations."""

    @pytest.mark.medium
    def test_retry_config_initialization(self):
        """Test that RetryConfig initializes with expected values."""
        config = RetryConfig(
            max_retries=5,
            initial_backoff=2.0,
            backoff_multiplier=3.0,
            max_backoff=30.0,
            jitter=False,
            exceptions_to_retry=[ValueError, TypeError],
        )
        assert config.max_retries == 5
        assert config.initial_backoff == 2.0
        assert config.backoff_multiplier == 3.0
        assert config.max_backoff == 30.0
        assert config.jitter is False
        assert config.exceptions_to_retry == [ValueError, TypeError]

    @pytest.mark.medium
    def test_default_retry_config(self):
        """Test that DEFAULT_RETRY_CONFIG has expected values."""
        assert DEFAULT_RETRY_CONFIG.max_retries == 3
        assert DEFAULT_RETRY_CONFIG.initial_backoff == 1.0
        assert DEFAULT_RETRY_CONFIG.backoff_multiplier == 2.0
        assert DEFAULT_RETRY_CONFIG.max_backoff == 60.0
        assert DEFAULT_RETRY_CONFIG.jitter is True
        assert DEFAULT_RETRY_CONFIG.exceptions_to_retry is None

    @pytest.mark.medium
    def test_quick_retry_config(self):
        """Test that QUICK_RETRY_CONFIG has expected values."""
        assert QUICK_RETRY_CONFIG.max_retries == 5
        assert QUICK_RETRY_CONFIG.initial_backoff == 0.1
        assert QUICK_RETRY_CONFIG.backoff_multiplier == 1.5
        assert QUICK_RETRY_CONFIG.max_backoff == 5.0
        assert QUICK_RETRY_CONFIG.jitter is True


class TestRetryMemoryOperation:
    """DTO-focused tests for the memory retry helper."""

    @pytest.mark.medium
    def test_retry_memory_operation_preserves_memory_record(self):
        """Decorated callables emit the original ``MemoryRecord`` DTO."""

        record = MemoryRecord(
            item=MemoryItem(
                id="abc",
                content="payload",
                memory_type=MemoryType.WORKING,
            ),
            source="primary",
        )

        @retry_memory_operation(max_retries=0)
        def emit_record() -> MemoryRecord:
            return record

        assert emit_record() is record

    @pytest.mark.medium
    def test_retry_memory_operation_condition_receives_payload_union(self):
        """Condition callbacks receive DTO-union payloads (``None`` when absent)."""

        captured: list[object] = []

        def callback(error: Exception, attempt: int, payload: object) -> bool:
            captured.append(payload)
            return False

        failing = MagicMock(side_effect=ValueError("boom"))
        decorated = retry_memory_operation(
            max_retries=0,
            condition_callbacks=[callback],
        )(failing)

        with pytest.raises(ValueError, match="boom"):
            decorated()

        assert captured == [None]
        assert QUICK_RETRY_CONFIG.exceptions_to_retry is None

    @pytest.mark.medium
    def test_persistent_retry_config(self):
        """Test that PERSISTENT_RETRY_CONFIG has expected values."""
        assert PERSISTENT_RETRY_CONFIG.max_retries == 10
        assert PERSISTENT_RETRY_CONFIG.initial_backoff == 2.0
        assert PERSISTENT_RETRY_CONFIG.backoff_multiplier == 2.0
        assert PERSISTENT_RETRY_CONFIG.max_backoff == 300.0
        assert PERSISTENT_RETRY_CONFIG.jitter is True
        assert PERSISTENT_RETRY_CONFIG.exceptions_to_retry is None

    @pytest.mark.medium
    def test_network_retry_config(self):
        """Test that NETWORK_RETRY_CONFIG has expected values."""
        assert NETWORK_RETRY_CONFIG.max_retries == 5
        assert NETWORK_RETRY_CONFIG.initial_backoff == 1.0
        assert NETWORK_RETRY_CONFIG.backoff_multiplier == 2.0
        assert NETWORK_RETRY_CONFIG.max_backoff == 60.0
        assert NETWORK_RETRY_CONFIG.jitter is True
        assert ConnectionError in NETWORK_RETRY_CONFIG.exceptions_to_retry
        assert TimeoutError in NETWORK_RETRY_CONFIG.exceptions_to_retry
        assert OSError in NETWORK_RETRY_CONFIG.exceptions_to_retry


class TestWithRetry:
    """Tests for the with_retry decorator."""

    @pytest.mark.medium
    def test_with_retry_default_config(self):
        """Test that with_retry uses DEFAULT_RETRY_CONFIG by default."""
        with patch(
            "devsynth.application.memory.retry.retry_with_backoff"
        ) as mock_retry:
            mock_retry.return_value = lambda f: f

            @with_retry()
            def dummy_func(self):
                return "success"

            mock_retry.assert_called_once_with(
                max_retries=DEFAULT_RETRY_CONFIG.max_retries,
                initial_backoff=DEFAULT_RETRY_CONFIG.initial_backoff,
                backoff_multiplier=DEFAULT_RETRY_CONFIG.backoff_multiplier,
                max_backoff=DEFAULT_RETRY_CONFIG.max_backoff,
                jitter=DEFAULT_RETRY_CONFIG.jitter,
                exceptions_to_retry=DEFAULT_RETRY_CONFIG.exceptions_to_retry,
                condition_callbacks=DEFAULT_RETRY_CONFIG.condition_callbacks,
                retry_conditions=DEFAULT_RETRY_CONFIG.retry_conditions,
                circuit_breaker_name=DEFAULT_RETRY_CONFIG.circuit_breaker_name,
                circuit_breaker_failure_threshold=DEFAULT_RETRY_CONFIG.circuit_breaker_failure_threshold,
                circuit_breaker_reset_timeout=DEFAULT_RETRY_CONFIG.circuit_breaker_reset_timeout,
            )

    @pytest.mark.medium
    def test_with_retry_custom_config(self):
        """Test that with_retry uses the provided RetryConfig."""
        custom_config = RetryConfig(
            max_retries=7,
            initial_backoff=0.5,
            backoff_multiplier=1.5,
            max_backoff=10.0,
            jitter=False,
            exceptions_to_retry=[ValueError],
        )
        with patch(
            "devsynth.application.memory.retry.retry_with_backoff"
        ) as mock_retry:
            mock_retry.return_value = lambda f: f

            @with_retry(custom_config)
            def dummy_func(self):
                return "success"

            mock_retry.assert_called_once_with(
                max_retries=custom_config.max_retries,
                initial_backoff=custom_config.initial_backoff,
                backoff_multiplier=custom_config.backoff_multiplier,
                max_backoff=custom_config.max_backoff,
                jitter=custom_config.jitter,
                exceptions_to_retry=custom_config.exceptions_to_retry,
                condition_callbacks=custom_config.condition_callbacks,
                retry_conditions=custom_config.retry_conditions,
                circuit_breaker_name=custom_config.circuit_breaker_name,
                circuit_breaker_failure_threshold=custom_config.circuit_breaker_failure_threshold,
                circuit_breaker_reset_timeout=custom_config.circuit_breaker_reset_timeout,
            )
