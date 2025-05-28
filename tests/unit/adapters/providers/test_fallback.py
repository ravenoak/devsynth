
import pytest
from unittest.mock import Mock, patch, call
import time

# Import the function to test
# Update the import path if needed
from devsynth.fallback import retry_with_exponential_backoff

@pytest.fixture
def mock_function():
    mock = Mock(side_effect=[ValueError("Test error"), ValueError("Test error"), "success"])
    mock.__name__ = "mock_function"
    return mock

def test_retry_with_exponential_backoff_success(mock_function):
    """Test that the function retries and eventually succeeds."""
    # Apply the decorator to the mock function
    decorated_func = retry_with_exponential_backoff(max_retries=3, initial_delay=0.1)(mock_function)

    # Call the decorated function
    result = decorated_func()

    # Check that the function was called 3 times
    assert mock_function.call_count == 3
    # Check that the final result is correct
    assert result == "success"

def test_retry_with_exponential_backoff_failure():
    """Test that the function raises an exception after max_retries."""
    # Create a mock function that always raises an error
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"

    # Apply the decorator to the mock function
    decorated_func = retry_with_exponential_backoff(max_retries=3, initial_delay=0.1)(mock_func)

    # Call the decorated function and expect it to raise an exception
    with pytest.raises(ValueError):
        decorated_func()

    # Check that the function was called max_retries + 1 times
    assert mock_func.call_count == 4

def test_retry_with_exponential_backoff_jitter():
    """Test that the function applies jitter to the delay."""
    # Create a mock function that always raises an error
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"

    # Mock the time.sleep function to capture the delay values
    sleep_times = []

    def mock_sleep(seconds):
        sleep_times.append(seconds)

    # Apply the decorator to the mock function
    with patch("time.sleep", side_effect=mock_sleep):
        decorated_func = retry_with_exponential_backoff(max_retries=3, initial_delay=1.0, max_delay=10.0, jitter=True)(mock_func)

        # Call the decorated function and expect it to raise an exception
        with pytest.raises(ValueError):
            decorated_func()

    # Check that the delays are different (due to jitter)
    assert len(sleep_times) == 3  # max_retries

    # The implementation uses the formula: delay * exponential_base * (0.5 + random.random())
    # For initial_delay=1.0 and exponential_base=2.0:
    # First delay: 1.0 * 2.0 * (0.5 to 1.5) = 1.0 to 3.0
    # Second delay: (1.0 to 3.0) * 2.0 * (0.5 to 1.5) = 1.0 to 9.0
    # Third delay: capped by max_delay=10.0
    assert 1.0 <= sleep_times[0] <= 3.0  # initial_delay * exponential_base * (0.5 + random.random())
    assert 1.0 <= sleep_times[1] <= 9.0  # previous_delay * exponential_base * (0.5 + random.random())
    assert 1.0 <= sleep_times[2] <= 10.0  # capped by max_delay

def test_retry_with_exponential_backoff_on_retry_callback():
    """Test that the on_retry callback is called on each retry attempt."""
    # Create a mock function that always raises an error
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"

    # Create a mock on_retry callback
    on_retry_mock = Mock()

    # Apply the decorator to the mock function with the on_retry callback
    with patch("time.sleep"):  # Mock sleep to avoid waiting
        decorated_func = retry_with_exponential_backoff(
            max_retries=3, 
            initial_delay=0.1, 
            on_retry=on_retry_mock
        )(mock_func)

        # Call the decorated function and expect it to raise an exception
        with pytest.raises(ValueError):
            decorated_func()

    # Check that the on_retry callback was called for each retry attempt
    assert on_retry_mock.call_count == 3  # Called once for each retry

    # Check that the callback was called with the correct arguments
    # The callback should be called with (exception, retry_number, delay)
    assert isinstance(on_retry_mock.call_args_list[0][0][0], ValueError)  # First arg is exception
    assert on_retry_mock.call_args_list[0][0][1] == 1  # Second arg is retry number
    assert isinstance(on_retry_mock.call_args_list[0][0][2], float)  # Third arg is delay

def test_retry_with_exponential_backoff_retryable_exceptions():
    """Test that only specified exceptions trigger retries."""
    # Create a mock function that raises different types of exceptions
    mock_func = Mock(side_effect=[
        ValueError("Test error"),  # Should be retried
        TypeError("Type error"),   # Should not be retried
        ValueError("Test error"),  # Should be retried
        "success"
    ])
    mock_func.__name__ = "mock_func"

    # Apply the decorator to the mock function with specific retryable exceptions
    with patch("time.sleep"):  # Mock sleep to avoid waiting
        decorated_func = retry_with_exponential_backoff(
            max_retries=3, 
            initial_delay=0.1, 
            retryable_exceptions=(ValueError,)  # Only retry ValueError
        )(mock_func)

        # Call the decorated function and expect it to raise TypeError
        with pytest.raises(TypeError):
            decorated_func()

    # Check that the function was called twice (initial call + 1 retry)
    # It should not retry after TypeError
    assert mock_func.call_count == 2

def test_retry_with_exponential_backoff_no_jitter():
    """Test that the function applies deterministic backoff when jitter is disabled."""
    # Create a mock function that always raises an error
    mock_func = Mock(side_effect=ValueError("Test error"))
    mock_func.__name__ = "mock_func"

    # Mock the time.sleep function to capture the delay values
    sleep_times = []

    def mock_sleep(seconds):
        sleep_times.append(seconds)

    # Apply the decorator to the mock function with jitter disabled
    with patch("time.sleep", side_effect=mock_sleep):
        decorated_func = retry_with_exponential_backoff(
            max_retries=3, 
            initial_delay=1.0, 
            exponential_base=2.0,
            max_delay=10.0, 
            jitter=False  # Disable jitter
        )(mock_func)

        # Call the decorated function and expect it to raise an exception
        with pytest.raises(ValueError):
            decorated_func()

    # Check that the delays follow a deterministic pattern
    assert len(sleep_times) == 3  # max_retries
    assert sleep_times[0] == 2.0  # initial_delay * exponential_base
    assert sleep_times[1] == 4.0  # previous_delay * exponential_base
    assert sleep_times[2] == 8.0  # previous_delay * exponential_base
