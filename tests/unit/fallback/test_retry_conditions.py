import pytest
from unittest.mock import Mock, patch

from devsynth.fallback import retry_with_exponential_backoff


def test_should_retry_prevents_retry():
    """Retry decorator should not retry when ``should_retry`` returns False.

    ReqID: FR-89"""
    mock_func = Mock(side_effect=Exception("boom"))
    mock_func.__name__ = "mock_func"

    decorated = retry_with_exponential_backoff(
        max_retries=3, initial_delay=0.1, should_retry=lambda exc: False
    )(mock_func)

    with pytest.raises(Exception):
        decorated()

    assert mock_func.call_count == 1


def test_should_retry_allows_retry_until_success():
    """Retry decorator retries when ``should_retry`` returns True.

    ReqID: FR-89"""
    mock_func = Mock(side_effect=[Exception("err"), Exception("err"), "ok"])
    mock_func.__name__ = "mock_func"

    decorated = retry_with_exponential_backoff(
        max_retries=5, initial_delay=0.0, should_retry=lambda exc: True
    )(mock_func)

    result = decorated()

    assert result == "ok"
    assert mock_func.call_count == 3


def test_retry_on_result_triggers_retry():
    mock_func = Mock(side_effect=["bad", "good"])
    mock_func.__name__ = "mock_func"

    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_on_result=lambda r: r == "bad",
    )(mock_func)

    result = decorated()

    assert result == "good"
    assert mock_func.call_count == 2


def test_retry_conditions_abort_when_condition_fails():
    mock_func = Mock(side_effect=Exception("boom"))
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_conditions=[lambda e: "retry" in str(e)],
    )(mock_func)
    with pytest.raises(Exception):
        decorated()
    assert mock_func.call_count == 1


def test_retry_conditions_allow_retry():
    mock_func = Mock(side_effect=[Exception("please retry"), "ok"])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_conditions=[lambda e: "retry" in str(e)],
    )(mock_func)
    result = decorated()
    assert result == "ok"
    assert mock_func.call_count == 2
