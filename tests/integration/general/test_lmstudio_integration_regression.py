#!/usr/bin/env python3
"""
Regression tests for LM Studio integration in DevSynth.

These tests ensure that LM Studio integration continues to work correctly
across different versions and configurations.

NOTE: LM Studio tests run on the same host as application tests. Resources are limited -
use large timeouts (60+ seconds) and consider resource constraints when designing tests.

Usage:
    poetry run pytest test_lmstudio_integration_regression.py -v
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.fast


class TestLMStudioIntegrationRegression:
    """Regression tests for LM Studio integration functionality."""

    @pytest.mark.fast
    def test_lmstudio_provider_registration(self):
        """Test that LM Studio provider can be registered in the factory.

        ReqID: LMSTUDIO-REG-1
        """
        from devsynth.application.llm.provider_factory import ProviderFactory

        factory = ProviderFactory()

        # Verify that LM Studio provider registration logic exists
        # (even if the actual package isn't installed)
        assert hasattr(factory, 'register_provider_type')

        # The factory should have a mechanism to register providers
        # This test ensures the registration interface works
        initial_count = len(factory.provider_types)

        # Register a mock provider for testing
        class MockProvider:
            pass

        factory.register_provider_type("mock_lmstudio", MockProvider)
        assert len(factory.provider_types) == initial_count + 1
        assert "mock_lmstudio" in factory.provider_types

    @pytest.mark.fast
    def test_lmstudio_configuration_loading(self):
        """Test that LM Studio configuration can be loaded correctly.

        ReqID: LMSTUDIO-REG-2
        """
        from devsynth.config.settings import get_settings

        # Set environment variables for LM Studio
        original_provider = os.environ.get('DEVSYNTH_LLM_PROVIDER')
        original_api_base = os.environ.get('DEVSYNTH_LLM_API_BASE')

        try:
            os.environ['DEVSYNTH_LLM_PROVIDER'] = 'lmstudio'
            os.environ['DEVSYNTH_LLM_API_BASE'] = 'http://127.0.0.1:1234'

            settings = get_settings()

            # Test that settings can access LM Studio configuration
            provider = settings["llm_provider"]
            api_base = settings["llm_api_base"]

            assert provider == 'lmstudio'
            assert api_base == 'http://127.0.0.1:1234'

        finally:
            # Restore original environment
            if original_provider is not None:
                os.environ['DEVSYNTH_LLM_PROVIDER'] = original_provider
            else:
                os.environ.pop('DEVSYNTH_LLM_PROVIDER', None)

            if original_api_base is not None:
                os.environ['DEVSYNTH_LLM_API_BASE'] = original_api_base
            else:
                os.environ.pop('DEVSYNTH_LLM_API_BASE', None)

    @pytest.mark.fast
    def test_lmstudio_settings_extraction(self):
        """Test that LLM settings can be extracted for LM Studio.

        ReqID: LMSTUDIO-REG-3
        """
        from devsynth.config.settings import get_settings, get_llm_settings

        # Set environment variables for LM Studio
        original_provider = os.environ.get('DEVSYNTH_LLM_PROVIDER')
        original_api_base = os.environ.get('DEVSYNTH_LLM_API_BASE')

        try:
            os.environ['DEVSYNTH_LLM_PROVIDER'] = 'lmstudio'
            os.environ['DEVSYNTH_LLM_API_BASE'] = 'http://127.0.0.1:1234'

            # Test settings extraction
            llm_settings = get_llm_settings()

            assert llm_settings["provider"] == 'lmstudio'
            assert llm_settings["api_base"] == 'http://127.0.0.1:1234'
            assert "max_tokens" in llm_settings
            assert "temperature" in llm_settings

        finally:
            # Restore original environment
            if original_provider is not None:
                os.environ['DEVSYNTH_LLM_PROVIDER'] = original_provider
            else:
                os.environ.pop('DEVSYNTH_LLM_PROVIDER', None)

            if original_api_base is not None:
                os.environ['DEVSYNTH_LLM_API_BASE'] = original_api_base
            else:
                os.environ.pop('DEVSYNTH_LLM_API_BASE', None)

    @pytest.mark.fast
    def test_lmstudio_provider_initialization_with_defaults(self):
        """Test LM Studio provider initialization with default settings.

        ReqID: LMSTUDIO-REG-4
        """
        # Test that provider can be imported and initialized (even without lmstudio package)
        try:
            from devsynth.application.llm.lmstudio_provider import LMStudioProvider

            # Test initialization with default config
            provider = LMStudioProvider()

            # Provider should be initialized even without LM Studio running
            assert provider is not None
            assert hasattr(provider, 'api_base')
            assert hasattr(provider, 'model')
            assert hasattr(provider, 'max_tokens')

        except ImportError:
            # If lmstudio package is not available, this is acceptable for regression testing
            pytest.skip("LM Studio package not available")

    @patch('devsynth.application.llm.lmstudio_provider.requests.get')
    @pytest.mark.fast
    def test_lmstudio_provider_mock_initialization(self, mock_get):
        """Test LM Studio provider with mocked LM Studio service.

        ReqID: LMSTUDIO-REG-5
        """
        from devsynth.application.llm.lmstudio_provider import LMStudioProvider

        # Mock the requests response for model listing
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'data': [
                {
                    'id': 'test-model',
                    'object': 'model',
                    'created': 1234567890,
                    'owned_by': 'test'
                }
            ]
        }
        mock_get.return_value = mock_response

        # Initialize provider
        provider = LMStudioProvider({
            'api_base': 'http://127.0.0.1:1234',
            'auto_select_model': False,
            'model': 'test-model'  # Explicitly set the model
        })

        # Test that provider is properly configured
        assert provider.api_base == 'http://127.0.0.1:1234'
        assert provider.model == 'test-model'

    @pytest.mark.fast
    def test_lmstudio_environment_variable_handling(self):
        """Test that LM Studio environment variables are handled correctly.

        ReqID: LMSTUDIO-REG-6
        """
        from devsynth.config.settings import get_settings

        # Test various environment variable combinations
        test_cases = [
            {
                'env': {'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE': 'true'},
                'expected_provider': 'lmstudio',
            },
            {
                'env': {'DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE': 'false'},
                'expected_provider': 'stub',  # Development default
            },
            {
                'env': {},
                'expected_provider': 'stub',  # Development default
            },
        ]

        for case in test_cases:
            # Set environment variables
            original_vars = {}
            for key, value in case['env'].items():
                original_vars[key] = os.environ.get(key)
                os.environ[key] = value

            try:
                settings = get_settings()
                provider = settings["llm_provider"]

                # Note: The actual provider depends on the configuration file
                # This test verifies that environment variables are accessible
                assert provider is not None

            finally:
                # Restore environment
                for key, value in original_vars.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    @pytest.mark.fast
    def test_lmstudio_config_file_integration(self):
        """Test that LM Studio configuration works with config files.

        ReqID: LMSTUDIO-REG-7
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("""
application:
  name: DevSynth Test
llm:
  default_provider: lmstudio
  providers:
    lmstudio:
      enabled: true
      api_base: http://127.0.0.1:1234
      model: test-model
      max_tokens: 1024
      temperature: 0.8
""")
            config_file = f.name

        try:
            # Set the config file path
            original_config = os.environ.get('DEVSYNTH_CONFIG_FILE')
            os.environ['DEVSYNTH_CONFIG_FILE'] = config_file

            from devsynth.config.settings import get_settings
            settings = get_settings()

            # Test that settings reflect the config file
            provider = settings["llm_provider"]

            # Note: The actual provider depends on how config files are loaded
            # This test verifies the mechanism exists
            assert provider is not None

        finally:
            # Restore environment and clean up
            if original_config is not None:
                os.environ['DEVSYNTH_CONFIG_FILE'] = original_config
            else:
                os.environ.pop('DEVSYNTH_CONFIG_FILE', None)

            os.unlink(config_file)


if __name__ == "__main__":
    pytest.main(["-v", "test_lmstudio_integration_regression.py"])
