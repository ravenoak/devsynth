import time
from unittest.mock import Mock

import pytest

from devsynth.fallback import retry_with_exponential_backoff


@pytest.mark.medium
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


@pytest.mark.medium
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


@pytest.mark.medium
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


@pytest.mark.medium
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


@pytest.mark.medium
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


@pytest.mark.medium
def test_string_condition_allows_retry():
    mock_func = Mock(side_effect=[Exception("please RETRY"), "ok"])
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_conditions=["RETRY"],
    )(mock_func)
    result = decorated()
    assert result == "ok"
    assert mock_func.call_count == 2


@pytest.mark.medium
def test_string_condition_aborts_when_missing():
    mock_func = Mock(side_effect=Exception("boom"))
    mock_func.__name__ = "mock_func"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=0,
        retry_conditions=["retry"],
    )(mock_func)
    with pytest.raises(Exception):
        decorated()
    assert mock_func.call_count == 1


@pytest.mark.medium
def test_exponential_backoff(monkeypatch):
    delays = []
    monkeypatch.setattr(time, "sleep", lambda d: delays.append(round(d, 2)))

    mock_func = Mock(side_effect=[Exception("err1"), Exception("err2"), "ok"])
    mock_func.__name__ = "mock_func"

    decorated = retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=0.1,
        exponential_base=2,
        jitter=False,
    )(mock_func)

    result = decorated()

    assert result == "ok"
    assert delays == [0.2, 0.4]


@pytest.mark.medium
def test_fallback_provider_order():
    from devsynth.adapters.provider_system import (
        BaseProvider,
        FallbackProvider,
        ProviderError,
    )

    provider1 = Mock(spec=BaseProvider)
    provider2 = Mock(spec=BaseProvider)
    provider1.complete.side_effect = ProviderError("p1 fail")
    provider2.complete.return_value = "ok"

    fallback = FallbackProvider(
        providers=[provider1, provider2],
        config={
            "fallback": {"enabled": True, "order": ["p1", "p2"]},
            "circuit_breaker": {"enabled": False},
            "retry": {
                "max_retries": 0,
                "initial_delay": 0,
                "exponential_base": 2,
                "max_delay": 1,
                "jitter": False,
                "track_metrics": False,
            },
        },
    )

    result = fallback.complete("prompt")

    assert result == "ok"
    provider1.complete.assert_called_once()
    provider2.complete.assert_called_once()
