from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("lmstudio")

pytestmark = [pytest.mark.requires_resource("lmstudio"), pytest.mark.medium]


@pytest.fixture()
def provider(lmstudio_stub):
    from devsynth.application.llm.lmstudio_provider import LMStudioProvider

    return LMStudioProvider(
        {
            "api_base": f"{lmstudio_stub.base_url}/v1",
            "model": "test-model",
            "auto_select_model": False,
        }
    )


@contextmanager
def tracker_patches():
    with (
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.__init__",
            return_value=None,
        ),
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.count_tokens",
            return_value=1,
        ),
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.ensure_token_limit",
            return_value=None,
        ),
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.count_conversation_tokens",
            return_value=1,
        ),
        patch(
            "devsynth.application.utils.token_tracker.TokenTracker.prune_conversation",
            side_effect=lambda messages, max_tokens: messages,
        ),
    ):
        yield


def test_generate_succeeds(provider):
    with tracker_patches():
        result = provider.generate("Test prompt")
    assert result == "This is a test response"


def test_generate_with_context_succeeds(provider):
    context = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    with tracker_patches():
        result = provider.generate_with_context("How are you?", context)
    assert result == "This is a test response"


def test_get_embedding_succeeds(provider):
    with patch(
        "devsynth.application.utils.token_tracker.TokenTracker.__init__",
        return_value=None,
    ):
        result = provider.get_embedding("Test text")
    assert result == [0.1, 0.2, 0.3, 0.4, 0.5]


def test_api_error_handling_raises_error(provider, lmstudio_stub):
    lmstudio_stub.trigger_error()
    with tracker_patches(), pytest.raises(Exception):
        provider.generate("Test prompt")


def test_circuit_breaker_opens_after_failures_fails(lmstudio_stub):
    from devsynth.application.llm.lmstudio_provider import (
        LMStudioConnectionError,
        LMStudioProvider,
    )

    with (
        patch("devsynth.application.llm.lmstudio_provider.lmstudio.llm") as mock_llm,
        patch(
            "devsynth.application.llm.lmstudio_provider.TokenTracker"
        ) as mock_tracker,
    ):
        mock_model = MagicMock()
        mock_model.complete.side_effect = Exception("fail")
        mock_llm.return_value = mock_model
        mock_tracker.return_value.count_tokens.return_value = 1
        mock_tracker.return_value.ensure_token_limit.return_value = None

        provider = LMStudioProvider(
            {
                "api_base": f"{lmstudio_stub.base_url}/v1",
                "model": "test-model",
                "auto_select_model": False,
                "max_retries": 2,
                "failure_threshold": 2,
                "recovery_timeout": 60,
            }
        )

        with pytest.raises(LMStudioConnectionError):
            provider.generate("Test prompt")
        call_count = mock_model.complete.call_count
        with pytest.raises(LMStudioConnectionError):
            provider.generate("Test prompt")
        assert mock_model.complete.call_count == call_count
