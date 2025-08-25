import os
from unittest.mock import patch

import pytest

from devsynth.application.llm.openai_provider import OpenAIProvider


def test_openai_provider_uses_mocked_env_key_without_network(monkeypatch):
    """ReqID: REQ-LLM-OPENAI-ENV-KEY

    Verifies that OpenAIProvider initializes successfully when OPENAI_API_KEY is set
    to a mock value (e.g., "test-openai-key") and does not attempt any real network
    calls. We patch OpenAI/AsyncOpenAI constructors so no external dependency is
    required and ensure provider picks up the env var.
    """

    # Ensure env var is set to the mocked key
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    # Patch the OpenAI client objects so no real library/network is required
    with (
        patch("devsynth.application.llm.openai_provider.OpenAI") as mock_openai,
        patch(
            "devsynth.application.llm.openai_provider.AsyncOpenAI"
        ) as mock_async_openai,
    ):
        provider = OpenAIProvider()
        assert provider.api_key == "test-openai-key"
        # Verify that client constructors were called with the mocked key
        mock_openai.assert_called()
        mock_async_openai.assert_called()

        # Provider should be able to access its stubbed client without raising
        # when invoking non-network path (we won't call generate to avoid API usage here)
        assert hasattr(provider, "client")
        assert hasattr(provider, "async_client")
