
import pytest
from unittest.mock import Mock, patch
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
