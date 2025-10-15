"""
Cross-provider consistency tests for LLM providers.

These tests verify that all LLM providers (OpenRouter, OpenAI, LM Studio)
implement identical interfaces and behave consistently across all functionality.
"""

import os
import pytest

from devsynth.application.llm.providers import get_llm_provider
from devsynth.exceptions import DevSynthError


def _is_provider_available(provider_name: str) -> bool:
    """Check if a provider is available for testing."""
    if provider_name == "openrouter":
        return "OPENROUTER_API_KEY" in os.environ
    elif provider_name == "openai":
        return "OPENAI_API_KEY" in os.environ
    elif provider_name == "lmstudio":
        return _is_lmstudio_available()
    elif provider_name == "offline":
        return True  # Offline provider is always available
    return False


def _is_lmstudio_available() -> bool:
    """Check if LM Studio server is available."""
    try:
        import httpx
        response = httpx.get("http://localhost:1234/v1/models", timeout=1)
        return response.status_code == 200
    except Exception:
        return False


class TestProviderInterfaceConsistency:
    """Test that all providers implement identical interfaces."""

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_provider_has_required_methods(self, provider_name):
        """Test that all providers have required core methods."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not _is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # All should have these core methods
            assert hasattr(provider, 'generate'), f"{provider_name} missing generate method"
            assert hasattr(provider, 'generate_with_context'), f"{provider_name} missing generate_with_context method"
            assert hasattr(provider, 'get_embedding'), f"{provider_name} missing get_embedding method"

            # Test identical behavior - basic generation
            response = provider.generate("Hello")
            assert isinstance(response, str), f"{provider_name} generate() should return string"
            assert len(response) > 0, f"{provider_name} generate() should return non-empty string"

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_provider_method_signatures_consistent(self, provider_name):
        """Test that provider methods have consistent signatures."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # Check method signatures are compatible
            import inspect

            generate_sig = inspect.signature(provider.generate)
            context_sig = inspect.signature(provider.generate_with_context)
            embedding_sig = inspect.signature(provider.get_embedding)

            # All methods should accept prompt as first parameter
            generate_params = list(generate_sig.parameters.keys())
            context_params = list(context_sig.parameters.keys())
            embedding_params = list(embedding_sig.parameters.keys())

            assert "prompt" in generate_params, f"{provider_name}.generate() missing prompt parameter"
            assert "prompt" in context_params, f"{provider_name}.generate_with_context() missing prompt parameter"
            assert "text" in embedding_params, f"{provider_name}.get_embedding() missing text parameter"

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_provider_error_handling_consistency(self, provider_name):
        """Test that providers handle errors consistently."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # Test invalid parameters - should raise consistent errors
            with pytest.raises(DevSynthError):
                provider.generate("", {"temperature": -1})  # Invalid temperature

            with pytest.raises(DevSynthError):
                provider.generate("test", {"max_tokens": 0})  # Invalid max_tokens

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise


class TestProviderErrorConsistency:
    """Test error handling consistency across providers."""

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_authentication_error_consistency(self, provider_name):
        """Test that authentication errors are consistent."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            # Use invalid API key to trigger authentication error
            config = {"api_key": "invalid-key-for-testing"}

            if provider_name == "openrouter":
                config["openrouter_api_key"] = "invalid-key-for-testing"
            elif provider_name == "openai":
                config["api_key"] = "invalid-key-for-testing"
            elif provider_name == "lmstudio":
                config["base_url"] = "http://localhost:1234/v1"

            provider = get_llm_provider({"provider": provider_name, **config})

            with pytest.raises(DevSynthError) as exc_info:
                provider.generate("Hello")

            # Error message should be descriptive and consistent
            error_msg = str(exc_info.value).lower()
            assert "error" in error_msg, f"{provider_name} error message should contain 'error'"

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_configuration_error_consistency(self, provider_name):
        """Test that configuration errors are consistent."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # Test invalid configuration parameters
            with pytest.raises(DevSynthError):
                provider.generate("test", {"temperature": 5.0})  # Invalid temperature

            with pytest.raises(DevSynthError):
                provider.generate("test", {"max_tokens": -1})  # Invalid max_tokens

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise


class TestProviderConfigurationConsistency:
    """Test configuration consistency across providers."""

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_standardized_config_acceptance(self, provider_name):
        """Test that all providers accept standardized configuration."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            # Standard configuration that should work for all providers
            config = {
                "provider": provider_name,
                "temperature": 0.7,
                "max_tokens": 1000,
                "timeout": 30,
            }

            # Add provider-specific keys if needed
            if provider_name == "openrouter":
                config["openrouter_api_key"] = "test-key"
            elif provider_name == "openai":
                config["api_key"] = "test-key"
            elif provider_name == "lmstudio":
                config["base_url"] = "http://localhost:1234/v1"

            provider = get_llm_provider(config)

            # Verify configuration was applied
            assert provider.temperature == 0.7
            assert provider.max_tokens == 1000

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_environment_variable_consistency(self, provider_name):
        """Test environment variable handling consistency."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            # Set environment variables for each provider
            env_vars = {}
            if provider_name == "openrouter":
                env_vars["OPENROUTER_API_KEY"] = "test-key"
            elif provider_name == "openai":
                env_vars["OPENAI_API_KEY"] = "test-key"
            elif provider_name == "lmstudio":
                env_vars["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "true"

            with pytest.MonkeyPatch().context() as m:
                for key, value in env_vars.items():
                    m.setenv(key, value)

                provider = get_llm_provider({"provider": provider_name})

                # Should initialize successfully with environment variables
                assert provider is not None

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise


class TestProviderPerformanceConsistency:
    """Test performance consistency across providers."""

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_response_time_consistency(self, provider_name):
        """Test response time characteristics across providers."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            import time

            provider = get_llm_provider({"provider": provider_name})

            # Measure response time for basic generation
            start_time = time.time()
            response = provider.generate("Performance consistency test")
            end_time = time.time()

            response_time = end_time - start_time

            # Response should be generated in reasonable time
            assert response_time < 30.0, f"{provider_name} response time too slow: {response_time}s"
            assert response_time > 0.001, f"{provider_name} response time suspiciously fast: {response_time}s"

            # Response should be valid
            assert isinstance(response, str)
            assert len(response) > 0

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_token_usage_consistency(self, provider_name):
        """Test token usage tracking consistency."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # Verify token tracker is available
            assert hasattr(provider, 'token_tracker'), f"{provider_name} missing token tracker"
            assert provider.token_tracker is not None, f"{provider_name} token tracker not initialized"

            # Test token counting functionality
            test_prompt = "This is a test prompt for token counting."
            token_count = provider.token_tracker.count_tokens(test_prompt)

            assert isinstance(token_count, int), f"{provider_name} token count should be integer"
            assert token_count > 0, f"{provider_name} token count should be positive"

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise


class TestProviderBehaviorConsistency:
    """Test behavioral consistency across providers."""

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_generation_behavior_consistency(self, provider_name):
        """Test that generation behavior is consistent across providers."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # Test basic generation
            response = provider.generate("Say 'Hello World'")

            # All providers should return strings
            assert isinstance(response, str), f"{provider_name} should return string"

            # Response should be reasonable length
            assert 0 < len(response) < 10000, f"{provider_name} response length out of range"

            # Should contain expected content (allowing for some variation)
            response_lower = response.lower()
            assert any(term in response_lower for term in ["hello", "world", "hi", "greetings"]), \
                f"{provider_name} response should contain greeting terms"

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    @pytest.mark.parametrize("provider_name", ["openrouter", "openai", "lmstudio", "offline"])
    def test_context_behavior_consistency(self, provider_name):
        """Test that context handling behavior is consistent."""
        # Skip providers that require external resources unless available
        if provider_name in ["openrouter", "openai"] and not self._is_provider_available(provider_name):
            pytest.skip(f"{provider_name} provider not available")

        if provider_name == "lmstudio" and not _is_lmstudio_available():
            pytest.skip("LM Studio server not available")

        try:
            provider = get_llm_provider({"provider": provider_name})

            # Test context-aware generation
            context = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"},
            ]

            response = provider.generate_with_context("Explain it simply.", context)

            # All providers should return strings
            assert isinstance(response, str), f"{provider_name} should return string"

            # Response should be reasonable length
            assert 0 < len(response) < 10000, f"{provider_name} response length out of range"

            # Should contain relevant terms (allowing for variation)
            response_lower = response.lower()
            assert any(term in response_lower for term in ["python", "programming", "language", "code", "syntax"]), \
                f"{provider_name} response should contain programming terms"

        except DevSynthError as e:
            # Some providers might fail due to missing configuration
            if "API key" in str(e) or "not configured" in str(e).lower():
                pytest.skip(f"{provider_name} provider requires configuration")
            raise

    def _is_provider_available(self, provider_name: str) -> bool:
        """Check if a provider is available for testing."""
        if provider_name == "openrouter":
            return "OPENROUTER_API_KEY" in os.environ
        elif provider_name == "openai":
            return "OPENAI_API_KEY" in os.environ
        elif provider_name == "lmstudio":
            return _is_lmstudio_available()
        elif provider_name == "offline":
            return True  # Offline provider is always available
        return False

    def _is_lmstudio_available(self) -> bool:
        """Check if LM Studio server is available."""
        try:
            import httpx
            response = httpx.get("http://localhost:1234/v1/models", timeout=1)
            return response.status_code == 200
        except Exception:
            return False
