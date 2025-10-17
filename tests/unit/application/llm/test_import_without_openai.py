import importlib

import pytest


@pytest.mark.fast
def test_import_openai_provider_without_openai_succeeds():
    """Importing OpenAI provider should succeed without openai installed."""
    # This test verifies that the provider module can be imported even when
    # OpenAI is not available, which is handled gracefully in the module

    # The module handles missing OpenAI dependency gracefully by setting
    # OpenAI and AsyncOpenAI to object when the import fails
    module = importlib.import_module("devsynth.application.llm.openai_provider")
    assert module.OpenAI is object
    assert module.AsyncOpenAI is object


@pytest.mark.fast
def test_openai_provider_requires_api_key(monkeypatch):
    """Missing API key should raise a clear error."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Import the module (it should handle missing OpenAI gracefully)
    module = importlib.import_module("devsynth.application.llm.openai_provider")

    # Test that instantiation fails with a clear error when no API key is provided
    with pytest.raises(module.OpenAIConnectionError) as exc:
        module.OpenAIProvider({})
    assert "OpenAI API key is required" in str(exc.value)
