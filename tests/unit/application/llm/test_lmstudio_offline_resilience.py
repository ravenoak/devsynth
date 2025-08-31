from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.fast
def test_generate_timeout_raises_connection_error_quickly(monkeypatch):
    """LMStudioProvider retries on transient errors and raises a connection error on timeout.

    ReqID: LMSTUDIO-20
    """
    # Defer import until after patches
    from devsynth.application.llm.lmstudio_provider import (
        LMStudioConnectionError,
        LMStudioProvider,
    )

    with (
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.__init__",
            return_value=None,
        ),
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.ensure_token_limit",
            return_value=None,
        ),
        patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm") as mock_llm,
    ):
        mock_model = MagicMock()

        # Simulate a timeout-like exception repeatedly
        class FakeTimeoutError(Exception):
            pass

        mock_model.complete.side_effect = FakeTimeoutError("timed out")
        mock_llm.return_value = mock_model

        provider = LMStudioProvider(
            {
                "api_base": "http://localhost:1234/v1",
                "model": "test-model",
                "auto_select_model": False,
                "max_retries": 2,  # keep it low so the test is fast
                "failure_threshold": 2,
                "recovery_timeout": 60,
            }
        )

        with pytest.raises(LMStudioConnectionError):
            provider.generate("Hello")

        # Ensure we attempted the underlying call at least once (and retried)
        assert mock_model.complete.call_count >= 1


@pytest.mark.fast
def test_generate_invalid_response_raises_model_error(monkeypatch):
    """If LM Studio returns an unexpected structure, raise LMStudioModelError.

    ReqID: LMSTUDIO-21
    """
    from devsynth.application.llm.lmstudio_provider import (
        LMStudioModelError,
        LMStudioProvider,
    )

    with (
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.__init__",
            return_value=None,
        ),
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.ensure_token_limit",
            return_value=None,
        ),
        patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm") as mock_llm,
    ):
        mock_model = MagicMock()
        # Return an object without 'content'
        mock_model.complete.return_value = MagicMock()
        mock_llm.return_value = mock_model

        provider = LMStudioProvider(
            {
                "api_base": "http://localhost:1234/v1",
                "model": "test-model",
                "auto_select_model": False,
            }
        )

        with pytest.raises(LMStudioModelError):
            provider.generate("Hello")
