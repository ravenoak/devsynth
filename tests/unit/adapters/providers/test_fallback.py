import time
from unittest.mock import Mock, call, patch

import pytest

from devsynth.fallback import retry_with_exponential_backoff


@pytest.fixture
def mock_function():
    mock = Mock(
        side_effect=[ValueError("Test error"), ValueError("Test error"), "success"]
    )
    mock.__name__ = "mock_function"
    return mock


@pytest.mark.medium
def test_retry_with_exponential_backoff_success_succeeds(mock_function):
    """Test that the function retries and eventually succeeds.

    ReqID: FR-89"""
    decorated_func = retry_with_exponential_backoff(max_retries=3, initial_delay=0.1)(
        mock_function
    )
    result = decorated_func()
    assert mock_function.call_count == 3
    assert result == "success"


@pytest.mark.medium
def test_retry_with_exponential_backoff_failure_raises_error():
    """Test that the function raises an exception after max_retries.

    ReqID: FR-89"""
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"
    decorated_func = retry_with_exponential_backoff(max_retries=3, initial_delay=0.1)(
        mock_func
    )
    with pytest.raises(ValueError):
        decorated_func()
    assert mock_func.call_count == 4


@pytest.mark.medium
def test_retry_with_exponential_backoff_jitter_succeeds():
    """Test that the function applies jitter to the delay.

    ReqID: FR-89"""
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"
    sleep_times = []

    def mock_sleep(seconds):
        sleep_times.append(seconds)

    with patch("time.sleep", side_effect=mock_sleep):
        decorated_func = retry_with_exponential_backoff(
            max_retries=3, initial_delay=1.0, max_delay=10.0, jitter=True
        )(mock_func)
        with pytest.raises(ValueError):
            decorated_func()
    assert len(sleep_times) == 3
    assert 1.0 <= sleep_times[0] <= 3.0
    assert 1.0 <= sleep_times[1] <= 9.0
    assert 1.0 <= sleep_times[2] <= 10.0


@pytest.mark.medium
def test_retry_with_exponential_backoff_on_retry_callback_succeeds():
    """Test that the on_retry callback is called on each retry attempt.

    ReqID: FR-89"""
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"
    on_retry_mock = Mock()
    with patch("time.sleep"):
        decorated_func = retry_with_exponential_backoff(
            max_retries=3, initial_delay=0.1, on_retry=on_retry_mock
        )(mock_func)
        with pytest.raises(ValueError):
            decorated_func()
    assert on_retry_mock.call_count == 3
    assert isinstance(on_retry_mock.call_args_list[0][0][0], ValueError)
    assert on_retry_mock.call_args_list[0][0][1] == 1
    assert isinstance(on_retry_mock.call_args_list[0][0][2], float)


@pytest.mark.medium
def test_retry_with_exponential_backoff_retryable_exceptions_raises_error():
    """Test that only specified exceptions trigger retries.

    ReqID: FR-89"""
    mock_func = Mock(
        side_effect=[
            ValueError("Test error"),
            TypeError("Type error"),
            ValueError("Test error"),
            "success",
        ]
    )
    mock_func.__name__ = "mock_func"
    with patch("time.sleep"):
        decorated_func = retry_with_exponential_backoff(
            max_retries=3, initial_delay=0.1, retryable_exceptions=(ValueError,)
        )(mock_func)
        with pytest.raises(TypeError):
            decorated_func()
    assert mock_func.call_count == 2


@pytest.mark.medium
def test_retry_with_exponential_backoff_no_jitter_succeeds():
    """Test that the function applies deterministic backoff when jitter is disabled.

    ReqID: FR-89"""
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"
    sleep_times = []

    def mock_sleep(seconds):
        sleep_times.append(seconds)

    with patch("time.sleep", side_effect=mock_sleep):
        decorated_func = retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False,
        )(mock_func)
        with pytest.raises(ValueError):
            decorated_func()
    assert len(sleep_times) == 3
    assert sleep_times[0] == 2.0
    assert sleep_times[1] == 4.0
    assert sleep_times[2] == 8.0
