from devsynth.adapters.provider_system import (
    ProviderFactory,
    OpenAIProvider,
    LMStudioProvider,
    get_provider_config,
)


def test_env_provider_openai_succeeds(monkeypatch):
    """Test that env provider openai succeeds.

    ReqID: N/A"""
    get_provider_config.cache_clear()
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = ProviderFactory.create_provider()
    assert isinstance(provider, OpenAIProvider)


def test_env_provider_lmstudio_succeeds(monkeypatch):
    """Test that env provider lmstudio succeeds.

    ReqID: N/A"""
    get_provider_config.cache_clear()
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "lmstudio")
    monkeypatch.setenv("LM_STUDIO_ENDPOINT", "http://localhost:8888")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = ProviderFactory.create_provider()
    assert isinstance(provider, LMStudioProvider)
