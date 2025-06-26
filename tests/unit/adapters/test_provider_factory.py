import logging
import pytest

from devsynth.adapters.provider_system import (
    ProviderFactory,
    ProviderType,
    LMStudioProvider,
    ProviderError,
    get_provider_config,
)


def test_create_provider_env_fallback(monkeypatch, caplog):
    """ProviderFactory should fall back to LMStudio when OPENAI_API_KEY is missing."""
    caplog.set_level(logging.WARNING)
    get_provider_config.cache_clear()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LM_STUDIO_ENDPOINT", "http://localhost:9999")
    provider = ProviderFactory.create_provider()
    assert isinstance(provider, LMStudioProvider)
    assert any("OpenAI API key not found" in rec.message for rec in caplog.records)


def test_explicit_openai_missing_key(monkeypatch):
    """Explicitly requesting OpenAI without an API key should raise an error."""
    get_provider_config.cache_clear()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LM_STUDIO_ENDPOINT", "http://localhost:9999")

    # Force LMStudio fallback to fail to surface the ProviderError
    def _raise(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "devsynth.adapters.provider_system.LMStudioProvider.__init__", _raise
    )
    with pytest.raises(ProviderError):
        ProviderFactory.create_provider(ProviderType.OPENAI.value)
