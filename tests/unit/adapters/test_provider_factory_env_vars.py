import os

import pytest

from devsynth.adapters.provider_system import (
    LMStudioProvider,
    OpenAIProvider,
    ProviderFactory,
    get_provider_config,
)

pytest.importorskip("lmstudio")
if not os.environ.get("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"):
    pytest.skip("LMStudio service not available", allow_module_level=True)

pytestmark = [pytest.mark.requires_resource("lmstudio")]


@pytest.mark.medium
def test_env_provider_openai_succeeds(monkeypatch):
    """Test that env provider openai succeeds.

    ReqID: N/A"""
    get_provider_config.cache_clear()
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    provider = ProviderFactory.create_provider()
    assert isinstance(provider, OpenAIProvider)


@pytest.mark.medium
def test_env_provider_lmstudio_succeeds(monkeypatch):
    """Test that env provider lmstudio succeeds.

    ReqID: N/A"""
    get_provider_config.cache_clear()
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "lmstudio")
    monkeypatch.setenv("LM_STUDIO_ENDPOINT", "http://localhost:8888")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = ProviderFactory.create_provider()
    assert isinstance(provider, LMStudioProvider)
