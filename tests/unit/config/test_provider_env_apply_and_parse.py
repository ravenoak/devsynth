import os

import pytest

from devsynth.config.provider_env import ProviderEnv


@pytest.mark.fast
def test_apply_to_env_sets_expected_vars(monkeypatch):
    # start with a clean environment for the vars under test
    for key in [
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
    ]:
        monkeypatch.delenv(key, raising=False)

    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    env.apply_to_env()

    assert os.environ["DEVSYNTH_PROVIDER"] == "stub"
    assert os.environ["DEVSYNTH_OFFLINE"] == "true"
    # Since the var was not set, apply_to_env should set it based on the value
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "false"


@pytest.mark.fast
def test_apply_to_env_does_not_override_explicit_lmstudio_flag(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")

    env = ProviderEnv(provider="openai", offline=False, lmstudio_available=False)
    env.apply_to_env()

    # Provider and offline are always applied
    assert os.environ["DEVSYNTH_PROVIDER"] == "openai"
    assert os.environ["DEVSYNTH_OFFLINE"] == "false"
    # But explicit availability flag must be preserved
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "true"


@pytest.mark.fast
def test_from_env_reads_current_environment(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "anthropic")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "yes")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "0")

    env = ProviderEnv.from_env()

    assert env.provider == "anthropic"
    assert env.offline is True
    assert env.lmstudio_available is False
