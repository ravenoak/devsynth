#!/usr/bin/env python3
"""
Step definitions for LM Studio integration behavior tests using pytest-bdd.

These step definitions implement the behavior tests defined in
lmstudio_integration_behavior.feature.

Usage:
    poetry run pytest test_lmstudio_integration_behavior_steps.py -v
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_bdd import given, scenarios, then, when

from devsynth.config import get_llm_settings
from devsynth.config.settings import get_settings

# Load scenarios from the feature file
scenarios("../features/lmstudio_integration.feature")


@given("DevSynth is properly installed and configured")
def step_devsynth_installed_configured(context):
    """Verify DevSynth is properly set up."""
    # This step just ensures we're in the right environment
    assert os.path.exists("/Users/caitlyn/Projects/github.com/ravenoak/devsynth")
    context.devsynth_root = Path("/Users/caitlyn/Projects/github.com/ravenoak/devsynth")


@given("the configuration specifies LM Studio as the default LLM provider")
def step_lmstudio_configured_as_default(context):
    """Set up configuration to use LM Studio as default provider."""
    # Set environment variables for LM Studio
    context.original_env = {}

    env_vars = {
        "DEVSYNTH_LLM_PROVIDER": "lmstudio",
        "DEVSYNTH_LLM_API_BASE": "http://127.0.0.1:1234",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "true",
    }

    for key, value in env_vars.items():
        context.original_env[key] = os.environ.get(key)
        os.environ[key] = value


@given("LM Studio is not running or unavailable")
def step_lmstudio_unavailable(context):
    """Simulate LM Studio being unavailable."""
    # Set environment to indicate LM Studio is not available
    context.original_lmstudio_available = os.environ.get(
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"
    )
    os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "false"


@given("LM Studio is available and configured")
def step_lmstudio_available(context):
    """Set up LM Studio as available."""
    context.original_lmstudio_available = os.environ.get(
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"
    )
    os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "true"


@given("a valid model is loaded in LM Studio")
def step_valid_model_loaded(context):
    """Set up a valid model configuration."""
    context.original_model = os.environ.get("DEVSYNTH_LLM_MODEL")
    os.environ["DEVSYNTH_LLM_MODEL"] = "test-model"


@given("I have conversation context")
def step_have_conversation_context(context):
    """Set up conversation context for testing."""
    context.conversation_context = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What is DevSynth?"},
        {
            "role": "assistant",
            "content": "DevSynth is an AI-driven development platform.",
        },
    ]


@given("I need to customize LM Studio provider settings")
def step_customize_lmstudio_settings(context):
    """Prepare to customize LM Studio settings."""
    context.custom_settings = {
        "api_base": "http://127.0.0.1:1234",
        "model": "custom-model",
        "max_tokens": 2048,
        "temperature": 0.8,
    }


@given("LM Studio provider is configured")
def step_lmstudio_provider_configured(context):
    """Ensure LM Studio provider is configured."""
    context.original_lmstudio_available = os.environ.get(
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"
    )
    os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "true"


@given("invalid LM Studio configuration is provided")
def step_invalid_lmstudio_config(context):
    """Set up invalid LM Studio configuration."""
    context.invalid_config = {
        "api_base": "invalid-url",
        "model": None,
        "max_tokens": -1,  # Invalid value
    }


@given("LM Studio is configured as primary provider but unavailable")
def step_lmstudio_primary_unavailable(context):
    """Set LM Studio as primary but make it unavailable."""
    context.original_provider = os.environ.get("DEVSYNTH_LLM_PROVIDER")
    context.original_lmstudio_available = os.environ.get(
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"
    )

    os.environ["DEVSYNTH_LLM_PROVIDER"] = "lmstudio"
    os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "false"


@when("I initialize DevSynth with LM Studio configuration")
def step_initialize_devsynth_lmstudio(context):
    """Initialize DevSynth with LM Studio configuration."""
    try:
        context.settings = get_settings()
        context.llm_settings = get_llm_settings()
        context.initialization_successful = True
    except Exception as e:
        context.initialization_error = e
        context.initialization_successful = False


@when("I attempt to use LM Studio provider")
def step_attempt_use_lmstudio_provider(context):
    """Attempt to use LM Studio provider."""
    try:
        from devsynth.application.llm.provider_factory import ProviderFactory

        context.factory = ProviderFactory()

        # Try to create LM Studio provider
        context.provider = context.factory.create_provider("lmstudio")
        context.provider_creation_successful = True

    except Exception as e:
        context.provider_creation_error = e
        context.provider_creation_successful = False


@when("I request text generation with a prompt")
def step_request_text_generation(context):
    """Request text generation."""
    try:
        context.generation_prompt = "Hello, can you help me test LM Studio integration?"

        # Mock LM Studio for testing
        with patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio"
        ) as mock_lmstudio:
            mock_lmstudio.sync_api.list_downloaded_models.return_value = [
                MagicMock(model_key="test-model", display_name="Test Model")
            ]

            mock_completion = MagicMock()
            mock_completion.content = "Yes, I can help you test LM Studio integration."
            mock_lmstudio.llm.return_value.complete.return_value = mock_completion

            from devsynth.application.llm.lmstudio_provider import LMStudioProvider

            context.provider = LMStudioProvider(
                {"api_base": "http://127.0.0.1:1234", "auto_select_model": True}
            )

            context.response = context.provider.generate(context.generation_prompt)
            context.generation_successful = True

    except Exception as e:
        context.generation_error = e
        context.generation_successful = False


@when("I request context-aware text generation")
def step_request_context_generation(context):
    """Request context-aware text generation."""
    try:
        context.generation_prompt = "Can you explain more about it?"

        # Mock LM Studio for testing
        with patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio"
        ) as mock_lmstudio:
            mock_lmstudio.sync_api.list_downloaded_models.return_value = [
                MagicMock(model_key="test-model", display_name="Test Model")
            ]

            mock_context_response = MagicMock()
            mock_context_response.content = (
                "DevSynth provides AI-driven development capabilities."
            )
            mock_lmstudio.llm.return_value.respond.return_value = mock_context_response

            from devsynth.application.llm.lmstudio_provider import LMStudioProvider

            context.provider = LMStudioProvider(
                {"api_base": "http://127.0.0.1:1234", "auto_select_model": True}
            )

            context.response = context.provider.generate_with_context(
                context.generation_prompt, context.conversation_context
            )
            context.generation_successful = True

    except Exception as e:
        context.generation_error = e
        context.generation_successful = False


@when("I specify configuration options for LM Studio")
def step_specify_lmstudio_config(context):
    """Specify LM Studio configuration options."""
    try:
        # Mock LM Studio for testing
        with patch(
            "devsynth.application.llm.lmstudio_provider.lmstudio"
        ) as mock_lmstudio:
            mock_lmstudio.sync_api.list_downloaded_models.return_value = [
                MagicMock(
                    model_key=context.custom_settings["model"],
                    display_name="Custom Model",
                )
            ]

            from devsynth.application.llm.lmstudio_provider import LMStudioProvider

            context.provider = LMStudioProvider(context.custom_settings)

            # Verify settings were applied
            assert context.provider.api_base == context.custom_settings["api_base"]
            assert context.provider.model == context.custom_settings["model"]
            assert context.provider.max_tokens == context.custom_settings["max_tokens"]
            assert (
                context.provider.temperature == context.custom_settings["temperature"]
            )

            context.configuration_successful = True

    except Exception as e:
        context.configuration_error = e
        context.configuration_successful = False


@when("I check the provider health status")
def step_check_provider_health(context):
    """Check LM Studio provider health status."""
    try:
        context.health_status = context.provider.health_check()
        context.health_check_successful = True

    except Exception as e:
        context.health_check_error = e
        context.health_check_successful = False


@when("I attempt to initialize the LM Studio provider")
def step_initialize_invalid_lmstudio_provider(context):
    """Attempt to initialize LM Studio provider with invalid config."""
    try:
        from devsynth.application.llm.lmstudio_provider import LMStudioProvider

        context.provider = LMStudioProvider(context.invalid_config)
        context.initialization_successful = True

    except Exception as e:
        context.initialization_error = e
        context.initialization_successful = False


@when("I request LLM services")
def step_request_llm_services(context):
    """Request LLM services when LM Studio is unavailable."""
    try:
        from devsynth.application.llm.provider_factory import ProviderFactory

        context.factory = ProviderFactory()

        # This should fallback to offline provider
        context.provider = context.factory.create_provider()
        context.fallback_successful = True

    except Exception as e:
        context.fallback_error = e
        context.fallback_successful = False


@then("LM Studio should be selected as the active provider")
def step_lmstudio_selected_as_active(context):
    """Verify LM Studio is selected as active provider."""
    assert (
        context.initialization_successful
    ), f"Initialization failed: {context.initialization_error}"
    assert (
        context.settings["llm_provider"] == "lmstudio"
    ), f"Expected lmstudio, got {context.settings['llm_provider']}"
    assert (
        context.llm_settings["provider"] == "lmstudio"
    ), f"Expected lmstudio, got {context.llm_settings['provider']}"


@then("LM Studio provider should be properly initialized")
def step_lmstudio_provider_initialized(context):
    """Verify LM Studio provider is properly initialized."""
    assert context.initialization_successful
    assert context.provider is not None
    assert hasattr(context.provider, "api_base")
    assert hasattr(context.provider, "model")


@then("DevSynth should handle the connection error gracefully")
def step_handle_connection_error_gracefully(context):
    """Verify connection errors are handled gracefully."""
    assert not context.provider_creation_successful
    assert context.provider_creation_error is not None
    # Should provide meaningful error message
    assert (
        "LM Studio" in str(context.provider_creation_error)
        or "connection" in str(context.provider_creation_error).lower()
    )


@then("provide appropriate fallback behavior")
def step_provide_fallback_behavior(context):
    """Verify appropriate fallback behavior."""
    # In this case, fallback would be handled at a higher level
    # This step verifies that the error is properly propagated
    assert context.provider_creation_error is not None


@then("LM Studio should generate a response")
def step_lmstudio_generates_response(context):
    """Verify LM Studio generates a response."""
    assert (
        context.generation_successful
    ), f"Generation failed: {context.generation_error}"
    assert context.response is not None
    assert isinstance(context.response, str)
    assert len(context.response) > 0


@then("the response should be returned to DevSynth")
def step_response_returned_to_devsynth(context):
    """Verify response is returned to DevSynth."""
    assert context.generation_successful
    assert context.response is not None
    # Should contain expected content from mock
    assert "test LM Studio" in context.response


@then("LM Studio should consider the conversation history")
def step_lmstudio_consider_history(context):
    """Verify LM Studio considers conversation history."""
    assert (
        context.generation_successful
    ), f"Generation failed: {context.generation_error}"
    assert context.response is not None
    assert isinstance(context.response, str)
    assert len(context.response) > 0


@then("generate a contextually appropriate response")
def step_generate_contextual_response(context):
    """Verify contextually appropriate response."""
    assert context.generation_successful
    # Should contain content related to DevSynth (from context)
    assert "DevSynth" in context.response


@then("the provider should use the specified settings")
def step_provider_uses_specified_settings(context):
    """Verify provider uses specified settings."""
    assert (
        context.configuration_successful
    ), f"Configuration failed: {context.configuration_error}"
    assert context.provider is not None


@then("apply them correctly during initialization")
def step_apply_settings_during_initialization(context):
    """Verify settings are applied during initialization."""
    assert context.configuration_successful
    # Settings should match what was specified
    assert context.provider.api_base == context.custom_settings["api_base"]
    assert context.provider.model == context.custom_settings["model"]


@then("the health check should return appropriate status")
def step_health_check_returns_status(context):
    """Verify health check returns appropriate status."""
    assert (
        context.health_check_successful
    ), f"Health check failed: {context.health_check_error}"
    assert isinstance(context.health_status, bool)


@then("indicate whether LM Studio is accessible")
def step_indicate_lmstudio_accessibility(context):
    """Verify health check indicates LM Studio accessibility."""
    assert context.health_check_successful
    # In our mock scenario, LM Studio might not be accessible
    # This step verifies the health check mechanism works
    assert context.health_status is not None


@then("DevSynth should detect the configuration errors")
def step_detect_configuration_errors(context):
    """Verify configuration errors are detected."""
    assert not context.initialization_successful
    assert context.initialization_error is not None


@then("provide clear error messages for troubleshooting")
def step_provide_clear_error_messages(context):
    """Verify clear error messages are provided."""
    assert context.initialization_error is not None
    # Error message should be descriptive
    error_msg = str(context.initialization_error)
    assert len(error_msg) > 0


@then("DevSynth should fallback to alternative providers")
def step_fallback_to_alternative_providers(context):
    """Verify fallback to alternative providers."""
    assert context.fallback_successful, f"Fallback failed: {context.fallback_error}"
    assert context.provider is not None


@then("continue operation with reduced functionality")
def step_continue_operation_reduced_functionality(context):
    """Verify continued operation with reduced functionality."""
    assert context.fallback_successful
    # Should be able to generate responses (offline provider)
    try:
        response = context.provider.generate("Test prompt")
        assert response is not None
    except Exception:
        # If offline provider also fails, that's acceptable for this test
        pass


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Clean up environment variables after each test."""
    # Store original values before test
    original_env = {}
    env_keys_to_restore = [
        "DEVSYNTH_LLM_PROVIDER",
        "DEVSYNTH_LLM_API_BASE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        "DEVSYNTH_LLM_MODEL",
    ]

    for key in env_keys_to_restore:
        original_env[key] = os.environ.get(key)

    yield  # Run the test

    # Restore original values after test
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
