import importlib

import pytest


def reload_provider_system():
    import devsynth.adapters.provider_system as ps

    reloaded = importlib.reload(ps)
    if hasattr(reloaded.get_provider_config, "cache_clear"):
        reloaded.get_provider_config.cache_clear()
    return reloaded


@pytest.mark.fast
def test_stub_provider_complete_and_embed_are_deterministic(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "stub")
    # Ensure providers not globally disabled
    monkeypatch.delenv("DEVSYNTH_DISABLE_PROVIDERS", raising=False)

    ps = reload_provider_system()

    provider = ps.ProviderFactory.create_provider()
    assert provider.__class__.__name__ == "StubProvider"

    text = "hello world"
    out1 = provider.complete(text, system_prompt="sys", max_tokens=100)
    out2 = provider.complete(text, system_prompt="sys", max_tokens=100)
    assert out1 == out2
    assert out1.startswith("[sys:sys] [stub:")
    assert text in out1

    emb1 = provider.embed(text)
    emb2 = provider.embed(text)
    assert emb1 == emb2
    assert isinstance(emb1, list) and isinstance(emb1[0], list)
    assert len(emb1[0]) == 8


@pytest.mark.fast
@pytest.mark.asyncio
async def test_stub_provider_async_matches_sync(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "stub")
    monkeypatch.delenv("DEVSYNTH_DISABLE_PROVIDERS", raising=False)

    ps = reload_provider_system()

    provider = ps.ProviderFactory.create_provider()
    out_sync = provider.complete("ping")
    out_async = await provider.acomplete("ping")
    assert out_sync == out_async

    emb_sync = provider.embed(["a", "b"])
    emb_async = await provider.aembed(["a", "b"])
    assert emb_sync == emb_async


@pytest.mark.fast
def test_provider_system_reload_preserves_settings_import(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "stub")
    monkeypatch.delenv("DEVSYNTH_DISABLE_PROVIDERS", raising=False)

    ps = reload_provider_system()

    from devsynth.config.settings import get_settings as reloaded_get_settings

    settings = reloaded_get_settings()
    assert settings is not None

    provider = ps.ProviderFactory.create_provider("stub")
    assert provider.__class__.__name__ == "StubProvider"
