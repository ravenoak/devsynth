import os

import pytest

from devsynth.config.provider_env import ProviderEnv


@pytest.mark.fast
def test_stub_provider_offline_defaults_to_stub():
    # Ensure offline mode defaults are applied
    env = ProviderEnv.from_env().with_test_defaults()
    mapping = env.as_dict()
    assert mapping["DEVSYNTH_OFFLINE"] == "true"
    # In test defaults, provider is 'stub' unless explicitly set
    assert mapping["DEVSYNTH_PROVIDER"] == "stub"


@pytest.mark.medium
@pytest.mark.requires_resource("openai")
def test_openai_live_profile_envs_well_formed(monkeypatch):
    # Validate that enabling openai live profile uses expected env flags
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv(
        "OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "test-openai-key")
    )
    # Default timeout if not set
    monkeypatch.setenv(
        "OPENAI_HTTP_TIMEOUT", os.environ.get("OPENAI_HTTP_TIMEOUT", "15")
    )
    env = ProviderEnv.from_env()
    assert env.provider == "openai"
    assert env.offline is False


@pytest.mark.medium
@pytest.mark.requires_resource("lmstudio")
def test_lmstudio_live_profile_envs_well_formed(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "lmstudio")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    # Default timeout if not set
    monkeypatch.setenv(
        "LM_STUDIO_ENDPOINT",
        os.environ.get("LM_STUDIO_ENDPOINT", "http://127.0.0.1:1234"),
    )
    monkeypatch.setenv(
        "LM_STUDIO_HTTP_TIMEOUT", os.environ.get("LM_STUDIO_HTTP_TIMEOUT", "15")
    )
    env = ProviderEnv.from_env()
    assert env.provider == "lmstudio"
    assert env.offline is False
