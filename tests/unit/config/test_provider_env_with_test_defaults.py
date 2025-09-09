import os

import pytest

from devsynth.config.provider_env import ProviderEnv


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_with_test_defaults_sets_offline_stub_and_openai_key(monkeypatch):
    # Ensure env is clean
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env = ProviderEnv.from_env().with_test_defaults()

    # Defaults
    assert env.provider == "stub"
    assert env.offline is True
    assert env.lmstudio_available is False

    # OPENAI_API_KEY placeholder is set deterministically
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


@pytest.mark.fast
def test_with_test_defaults_respects_explicit_provider(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)

    env = ProviderEnv.from_env().with_test_defaults()

    assert env.provider == "openai"
    # Even if provider is explicit, offline should default to True for tests when unset
    assert env.offline is True
