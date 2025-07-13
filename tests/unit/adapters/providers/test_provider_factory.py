import pytest
from devsynth.adapters.provider_system import (
    ProviderFactory,
    ProviderType,
    LMStudioProvider,
    OpenAIProvider,
)


def _config_without_openai_key():
    return {
        "default_provider": "openai",
        "openai": {
            "api_key": None,
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1",
        },
        "lmstudio": {"endpoint": "http://localhost:1234", "model": "default"},
    }


def _config_with_openai_key():
    return {
        "default_provider": "openai",
        "openai": {
            "api_key": "test",
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1",
        },
        "lmstudio": {"endpoint": "http://localhost:1234", "model": "default"},
    }


def test_create_provider_fallbacks_to_lmstudio_succeeds(monkeypatch):
    """Test that create provider fallbacks to lmstudio succeeds.

    ReqID: N/A"""
    monkeypatch.setattr(
        "devsynth.adapters.provider_system.get_provider_config",
        _config_without_openai_key,
    )
    provider = ProviderFactory.create_provider(ProviderType.OPENAI.value)
    assert isinstance(provider, LMStudioProvider)


def test_create_provider_default_with_missing_key_succeeds(monkeypatch):
    """Test that create provider default with missing key succeeds.

    ReqID: N/A"""
    monkeypatch.setattr(
        "devsynth.adapters.provider_system.get_provider_config",
        _config_without_openai_key,
    )
    provider = ProviderFactory.create_provider()
    assert isinstance(provider, LMStudioProvider)


def test_create_provider_openai_succeeds(monkeypatch):
    """Test that create provider openai succeeds.

    ReqID: N/A"""
    monkeypatch.setattr(
        "devsynth.adapters.provider_system.get_provider_config", _config_with_openai_key
    )
    provider = ProviderFactory.create_provider(ProviderType.OPENAI.value)
    assert isinstance(provider, OpenAIProvider)
