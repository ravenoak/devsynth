import logging
import os
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("lmstudio")
if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
    pytest.skip("LMStudio service not available", allow_module_level=True)

from devsynth.application.llm.offline_provider import OfflineProvider
from devsynth.exceptions import DevSynthError
from devsynth.metrics import get_retry_metrics, reset_metrics

# These unit tests execute quickly

pytestmark = [
    pytest.mark.requires_resource("lmstudio")
]  # speed markers on functions only


@pytest.mark.fast
def test_provider_logging_cleanup(lmstudio_service, capsys):
    """Providers should not log after logging.shutdown.

    ReqID: LMSTUDIO-13
    """
    from devsynth.application.llm.lmstudio_provider import LMStudioProvider

    OfflineProvider().generate("hello")
    with (
        patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm") as mock_llm,
        patch(
            "devsynth.application.llm.lmstudio_provider.TokenTracker"
        ) as mock_tracker,
    ):
        mock_model = MagicMock()
        mock_model.complete.return_value = MagicMock(content="ok")
        mock_llm.return_value = mock_model
        mock_tracker.return_value.count_tokens.return_value = 1
        mock_tracker.return_value.ensure_token_limit.return_value = None
        provider = LMStudioProvider({"auto_select_model": False})
        provider.generate("hi")

    lmstudio_module = pytest.importorskip("lmstudio")
    lmstudio_module.sync_api._reset_default_client()
    logging.shutdown()
    assert "I/O operation on closed file" not in capsys.readouterr().err


@pytest.mark.fast
def test_lmstudio_retry_metrics_and_circuit_breaker(lmstudio_service):
    """Failures increment retry metrics and open the circuit breaker.

    ReqID: LMSTUDIO-14
    """
    from devsynth.application.llm.lmstudio_provider import (
        LMStudioConnectionError,
        LMStudioProvider,
    )

    reset_metrics()
    with (
        patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm") as mock_llm,
        patch(
            "devsynth.application.llm.lmstudio_provider.TokenTracker"
        ) as mock_tracker,
    ):
        mock_model = MagicMock()
        mock_model.complete.side_effect = Exception("boom")
        mock_llm.return_value = mock_model
        mock_tracker.return_value.count_tokens.return_value = 1
        mock_tracker.return_value.ensure_token_limit.return_value = None

        provider = LMStudioProvider(
            {
                "auto_select_model": False,
                "max_retries": 2,
                "failure_threshold": 2,
                "recovery_timeout": 60,
            }
        )

        with pytest.raises(LMStudioConnectionError):
            provider.generate("hi")

        metrics = get_retry_metrics()
        assert metrics.get("attempt") == 2
        assert metrics.get("failure") == 1
        assert provider.circuit_breaker.state == provider.circuit_breaker.OPEN
        call_count = mock_model.complete.call_count

        with pytest.raises(LMStudioConnectionError):
            provider.generate("hi")

        assert mock_model.complete.call_count == call_count
        metrics = get_retry_metrics()
        assert metrics.get("failure") == 2
        assert metrics.get("attempt") == 4
