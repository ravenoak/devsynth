from pytest_bdd import given, when, then, parsers
from unittest.mock import Mock, patch
import pytest

# Import the function to test
# Update the import path if needed
from devsynth.fallback import retry_with_exponential_backoff


@pytest.fixture
def context():
    return {}


@pytest.mark.medium
@given("a function that fails 2 times and then succeeds")
def step_function_fails_then_succeeds(context):
    mock = Mock(
        side_effect=[ValueError("Test error"), ValueError("Test error"), "success"]
    )
    mock.__name__ = "mock_function"
    context["mock_function"] = mock


@pytest.mark.medium
@given("a function that always fails")
def step_function_always_fails(context):
    mock = Mock(side_effect=ValueError("Test error"))
    mock.__name__ = "mock_function"
    context["mock_function"] = mock


@pytest.mark.medium
@given("a function that raises different types of exceptions")
def step_function_raises_different_exceptions(context):
    mock = Mock(
        side_effect=[
            ValueError("Test error"),  # Should be retried
            TypeError("Type error"),  # Should not be retried
            ValueError("Test error"),  # Should be retried
            "success",
        ]
    )
    mock.__name__ = "mock_function"
    context["mock_function"] = mock


@pytest.mark.medium
@when(parsers.parse("I apply the retry decorator with max_retries={max_retries:d} and initial_delay={initial_delay:f}"))
def step_apply_retry_decorator(context, max_retries, initial_delay):
    context["decorated_function"] = retry_with_exponential_backoff(
        max_retries=max_retries, initial_delay=initial_delay
    )(context["mock_function"])


@pytest.mark.medium
@when(parsers.parse("I apply the retry decorator with max_retries={max_retries:d}, initial_delay={initial_delay:f}, and jitter={jitter}"))
def step_apply_retry_decorator_with_jitter(context, max_retries, initial_delay, jitter):
    # Convert string "True"/"False" to boolean
    jitter_bool = jitter.lower() == "true"
    context["sleep_times"] = []

    def mock_sleep(seconds):
        context["sleep_times"].append(seconds)

    context["sleep_patch"] = patch("time.sleep", side_effect=mock_sleep)
    context["sleep_mock"] = context["sleep_patch"].start()

    context["decorated_function"] = retry_with_exponential_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=10.0,
        jitter=jitter_bool,
    )(context["mock_function"])


@pytest.mark.medium
@when(parsers.parse("I apply the retry decorator with max_retries={max_retries:d}, initial_delay={initial_delay:f}, and a callback function"))
def step_apply_retry_decorator_with_callback(context, max_retries, initial_delay):
    # Create a mock callback function
    context["callback_mock"] = Mock()

    # Mock sleep to avoid waiting
    context["sleep_patch"] = patch("time.sleep")
    context["sleep_mock"] = context["sleep_patch"].start()

    context["decorated_function"] = retry_with_exponential_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        on_retry=context["callback_mock"],
    )(context["mock_function"])


@pytest.mark.medium
@when(parsers.parse("I apply the retry decorator with max_retries={max_retries:d}, initial_delay={initial_delay:f}, and retryable_exceptions={exceptions}"))
def step_apply_retry_decorator_with_exceptions(context, max_retries, initial_delay, exceptions):
    # Parse the exceptions string to get the actual exception types
    # For now, we only support ValueError
    if "ValueError" in exceptions:
        retryable_exceptions = (ValueError,)
    else:
        retryable_exceptions = (Exception,)
    
    # Mock sleep to avoid waiting
    context["sleep_patch"] = patch("time.sleep")
    context["sleep_mock"] = context["sleep_patch"].start()
    
    context["decorated_function"] = retry_with_exponential_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        retryable_exceptions=retryable_exceptions,
    )(context["mock_function"])


@pytest.mark.medium
@when("I call the decorated function")
def step_call_decorated_function(context):
    try:
        context["result"] = context["decorated_function"]()
        context["exception"] = None
    except Exception as e:
        context["exception"] = e

    # Clean up any patches
    if "sleep_patch" in context:
        context["sleep_patch"].stop()


@pytest.mark.medium
@then(parsers.parse("the function should be called {call_count:d} times"))
def step_check_call_count(context, call_count):
    assert context["mock_function"].call_count == call_count


@pytest.mark.medium
@then("the final result should be successful")
def step_check_successful_result(context):
    assert context["exception"] is None
    assert context["result"] == "success"


@pytest.mark.medium
@then("the function should raise an exception")
def step_check_exception(context):
    assert context["exception"] is not None
    assert isinstance(context["exception"], ValueError)


@pytest.mark.medium
@then("the function should raise a TypeError")
def step_check_type_error(context):
    assert context["exception"] is not None
    assert isinstance(context["exception"], TypeError)


@pytest.mark.medium
@then("the delays between retries should follow exponential backoff with jitter")
def step_check_exponential_backoff_with_jitter(context):
    sleep_times = context["sleep_times"]

    # Check that the delays are different (due to jitter)
    assert len(sleep_times) == 3  # max_retries

    # The implementation multiplies the previous delay by ``exponential_base``
    # and ``0.5 + random.random()``. We simply verify that delays stay within the
    # allowed range and are not constant.
    assert 1.0 <= sleep_times[0] <= 3.0
    assert 1.0 <= sleep_times[1] <= 9.0
    assert 1.0 <= sleep_times[2] <= 12.0
    assert len(set(sleep_times)) > 1  # jitter introduces variation


@pytest.mark.medium
@then("the delays between retries should follow deterministic exponential backoff")
def step_check_deterministic_exponential_backoff(context):
    sleep_times = context["sleep_times"]

    # Check that the delays follow a deterministic pattern
    assert len(sleep_times) == 3  # max_retries
    assert sleep_times[0] == 2.0  # initial_delay * exponential_base
    assert sleep_times[1] == 4.0  # previous_delay * exponential_base
    assert sleep_times[2] == 8.0  # previous_delay * exponential_base


@pytest.mark.medium
@then("the callback function should be called 3 times")
def step_check_callback_called(context):
    assert context["callback_mock"].call_count == 3


@pytest.mark.medium
@then("the callback function should receive the correct arguments")
def step_check_callback_arguments(context):
    # Check that the callback was called with the correct arguments
    # The callback should be called with (exception, retry_number, delay)
    assert isinstance(
        context["callback_mock"].call_args_list[0][0][0], ValueError
    )  # First arg is exception
    assert (
        context["callback_mock"].call_args_list[0][0][1] == 1
    )  # Second arg is retry number
    assert isinstance(
        context["callback_mock"].call_args_list[0][0][2], float
    )  # Third arg is delay
