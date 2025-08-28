from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from devsynth.application.llm.providers import LMStudioProvider


def _import_provider():
    from devsynth.application.llm.lmstudio_provider import LMStudioProvider

    return LMStudioProvider


class TestLMStudioStreaming:
    """Tests for LMStudioProvider using the mock service."""

    @pytest.mark.medium
    def test_generate_streaming_returns_expected(self, lmstudio_service):
        """Ensure generate handles streaming responses.

        ReqID: LMSTUDIO-11"""
        LMStudioProvider = _import_provider()
        with patch(
            "devsynth.application.llm.lmstudio_provider.get_llm_settings"
        ) as mock_settings:
            mock_settings.return_value = {
                "api_base": f"{lmstudio_service.base_url}/v1",
                "model": "test-model",
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": False,
            }
            provider = LMStudioProvider()
        result = provider.generate("Hello")
        assert result == "This is a test"

    @pytest.mark.medium
    def test_generate_with_context_streaming_returns_expected(self, lmstudio_service):
        """Ensure generate_with_context handles streaming responses.

        ReqID: LMSTUDIO-12"""
        LMStudioProvider = _import_provider()
        with patch(
            "devsynth.application.llm.lmstudio_provider.get_llm_settings"
        ) as mock_settings:
            mock_settings.return_value = {
                "api_base": f"{lmstudio_service.base_url}/v1",
                "model": "test-model",
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": False,
            }
            provider = LMStudioProvider()
        context = [{"role": "system", "content": "You are helpful."}]
        result = provider.generate_with_context("Hi", context)
        assert result == "This is a test"
