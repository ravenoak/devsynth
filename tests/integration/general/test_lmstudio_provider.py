import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.llm.providers import LMStudioProvider

pytestmark = pytest.mark.requires_resource("lmstudio")


def _import_provider():
    """Import provider components after any mocks are applied."""
    from devsynth.application.llm.lmstudio_provider import (
        LMStudioConnectionError,
        LMStudioModelError,
        LMStudioProvider,
    )

    return LMStudioProvider, LMStudioConnectionError, LMStudioModelError


class TestLMStudioProvider:
    """Tests for the LMStudioProvider class.

    ReqID: LMSTUDIO-1"""

    @pytest.mark.medium
    def test_init_with_default_config_succeeds(self, lmstudio_service):
        """Test initialization with default configuration.

        ReqID: LMSTUDIO-2"""
        LMStudioProvider, _, _ = _import_provider()
        with (
            patch(
                "devsynth.application.llm.lmstudio_provider.get_llm_settings"
            ) as mock_settings,
            patch(
                "devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models"
            ) as mock_list,
        ):
            mock_settings.return_value = {
                "api_base": "http://localhost:1234/v1",
                "model": None,
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": True,
            }
            mock_list.return_value = [{"id": "test_model", "name": "Test Model"}]
            provider = LMStudioProvider()
            assert provider.model == "test_model"
            assert provider.api_base == "http://localhost:1234/v1"
            assert provider.max_tokens == 1024

    @pytest.mark.medium
    def test_init_with_specified_model_succeeds(self, lmstudio_service):
        """Test initialization with a specified model.

        ReqID: LMSTUDIO-3"""
        LMStudioProvider, _, _ = _import_provider()
        provider = LMStudioProvider({"model": "specified_model"})
        assert provider.model == "specified_model"

    @pytest.mark.medium
    def test_init_with_connection_error_succeeds(self, lmstudio_service):
        """Test initialization when LM Studio is not available.

        ReqID: LMSTUDIO-4"""
        LMStudioProvider, LMStudioConnectionError, _ = _import_provider()
        with (
            patch(
                "devsynth.application.llm.lmstudio_provider.get_llm_settings"
            ) as mock_settings,
            patch(
                "devsynth.application.llm.lmstudio_provider.LMStudioProvider.list_available_models"
            ) as mock_list,
        ):
            mock_settings.return_value = {
                "api_base": "http://localhost:1234/v1",
                "model": None,
                "max_tokens": 1024,
                "temperature": 0.7,
                "auto_select_model": True,
            }
            mock_list.side_effect = LMStudioConnectionError("Connection error")
            provider = LMStudioProvider()
            assert provider.model == "local_model"

    @pytest.mark.medium
    def test_list_available_models_error_fails(self, lmstudio_service):
        """Test listing available models when the API call fails.

        ReqID: LMSTUDIO-5"""
        LMStudioProvider, LMStudioConnectionError, _ = _import_provider()
        with patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio.sync_api.list_downloaded_models"
        ) as mock_list:
            mock_list.side_effect = Exception("Internal server error")
            provider = LMStudioProvider({"auto_select_model": False})
            with pytest.raises(LMStudioConnectionError):
                provider.list_available_models()

    @pytest.mark.medium
    def test_list_available_models_integration_succeeds(self, lmstudio_service):
        """Integration test for listing available models from LM Studio.

        ReqID: LMSTUDIO-6"""
        LMStudioProvider, _, _ = _import_provider()
        if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
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
        else:
            provider = LMStudioProvider()
        models = provider.list_available_models()
        assert isinstance(models, list)
        if models:
            assert "id" in models[0]

    @pytest.mark.medium
    def test_generate_integration_succeeds(self, lmstudio_service):
        """Integration test for generating text from LM Studio.

        ReqID: LMSTUDIO-7"""
        LMStudioProvider, _, _ = _import_provider()
        if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
            with patch(
                "devsynth.application.llm.lmstudio_provider.get_llm_settings"
            ) as mock_settings:
                mock_settings.return_value = {
                    "api_base": f"{lmstudio_service.base_url}/v1",
                    "model": "test_model",
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "auto_select_model": False,
                }
                provider = LMStudioProvider()
        else:
            provider = LMStudioProvider()
        response = provider.generate("Hello, how are you?")
        assert isinstance(response, str)
        assert response == "This is a test response"

    @pytest.mark.medium
    def test_generate_with_connection_error_succeeds(self, lmstudio_service):
        """Test generating text when LM Studio is not available.

        ReqID: LMSTUDIO-8"""
        LMStudioProvider, LMStudioConnectionError, _ = _import_provider()
        # Patch the TokenTracker.__init__ method to avoid using tiktoken
        with (
            patch(
                "devsynth.application.utils.token_tracker.TokenTracker.__init__"
            ) as mock_init,
            patch(
                "devsynth.application.utils.token_tracker.TokenTracker.count_tokens"
            ) as mock_count,
            patch(
                "devsynth.application.utils.token_tracker.TokenTracker.ensure_token_limit"
            ) as mock_ensure,
            patch(
                "devsynth.application.llm.lmstudio_provider.lmstudio.llm"
            ) as mock_llm,
            patch(
                "devsynth.application.llm.lmstudio_provider.LMStudioProvider._execute_with_resilience"
            ) as mock_execute,
        ):

            # Make the __init__ method do nothing
            mock_init.return_value = None

            # Mock the token counting methods
            mock_count.return_value = 5
            mock_ensure.return_value = None

            # Mock the lmstudio client and _execute_with_resilience
            mock_llm.return_value.complete = MagicMock()
            mock_execute.side_effect = Exception("Connection error")

            provider = LMStudioProvider({"auto_select_model": False})
            with pytest.raises(LMStudioConnectionError):
                provider.generate("Hello, how are you?")

    @pytest.mark.medium
    def test_generate_with_invalid_response_returns_expected_result(
        self, lmstudio_service
    ):
        """Test generating text when LM Studio returns an invalid response.

        ReqID: LMSTUDIO-9"""
        LMStudioProvider, LMStudioConnectionError, LMStudioModelError = (
            _import_provider()
        )
        # Patch the TokenTracker.__init__ method to avoid using tiktoken
        with (
            patch(
                "devsynth.application.utils.token_tracker.TokenTracker.__init__"
            ) as mock_init,
            patch(
                "devsynth.application.utils.token_tracker.TokenTracker.count_tokens"
            ) as mock_count,
            patch(
                "devsynth.application.utils.token_tracker.TokenTracker.ensure_token_limit"
            ) as mock_ensure,
            patch(
                "devsynth.application.llm.lmstudio_provider.lmstudio.llm"
            ) as mock_llm,
            patch(
                "devsynth.application.llm.lmstudio_provider.LMStudioProvider._execute_with_resilience"
            ) as mock_execute,
        ):

            # Make the __init__ method do nothing
            mock_init.return_value = None

            # Mock the token counting methods
            mock_count.return_value = 5
            mock_ensure.return_value = None

            # Mock the lmstudio client and _execute_with_resilience
            mock_llm.return_value.complete = MagicMock()
            mock_execute.return_value = MagicMock(spec=[])

            provider = LMStudioProvider({"auto_select_model": False})
            with pytest.raises(LMStudioModelError):
                provider.generate("Hello, how are you?")

    @pytest.mark.medium
    def test_generate_with_context_integration_succeeds(self, lmstudio_service):
        """Integration test for generating text with context from LM Studio.

        ReqID: LMSTUDIO-10"""
        LMStudioProvider, _, _ = _import_provider()
        if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
            with patch(
                "devsynth.application.llm.lmstudio_provider.get_llm_settings"
            ) as mock_settings:
                mock_settings.return_value = {
                    "api_base": f"{lmstudio_service.base_url}/v1",
                    "model": "test_model",
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "auto_select_model": False,
                }
                provider = LMStudioProvider()
        else:
            provider = LMStudioProvider()
        context = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, who are you?"},
            {
                "role": "assistant",
                "content": "I'm an AI assistant. How can I help you?",
            },
        ]
        response = provider.generate_with_context(
            "Tell me more about yourself.", context
        )
        assert isinstance(response, str)
        assert response == "This is a test response"


if __name__ == "__main__":
    pytest.main(["-v", "test_lmstudio_provider.py"])
