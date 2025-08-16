from unittest.mock import Mock, patch

import pytest

from devsynth.fallback import reset_prometheus_metrics, retry_with_exponential_backoff
from devsynth.metrics import get_retry_condition_metrics, get_retry_metrics


class Response:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


@pytest.mark.fast
def test_retry_predicate_triggers_retry() -> None:
    reset_prometheus_metrics()
    responses = [Response(503), Response(200)]
    func = Mock(side_effect=lambda: responses.pop(0))
    func.__name__ = "http_call"
    decorated = retry_with_exponential_backoff(
        max_retries=2,
        initial_delay=1,
        jitter=False,
        retry_predicates={"server_error": lambda r: r.status_code >= 500},
        track_metrics=True,
    )(func)
    with patch("time.sleep") as sleep_mock:
        result = decorated()
    assert result.status_code == 200
    sleep_mock.assert_called_once_with(2)
    retry_metrics = get_retry_metrics()
    cond_metrics = get_retry_condition_metrics()
    assert retry_metrics.get("predicate") == 1
    assert retry_metrics.get("success") == 1
    assert cond_metrics.get("predicate:server_error:trigger") == 1
    assert cond_metrics.get("predicate:server_error:suppress") == 1
