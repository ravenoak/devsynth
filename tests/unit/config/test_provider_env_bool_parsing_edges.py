import os

import pytest

from devsynth.config.provider_env import ProviderEnv


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_from_env_parses_true_and_false_variants(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "On")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "No")
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")

    env = ProviderEnv.from_env()
    assert env.offline is True
    assert env.lmstudio_available is False
    assert env.provider == "openai"


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_from_env_unrecognized_values_fall_back_to_defaults(monkeypatch):
    # Unknown tokens should not coerce to True/False; they fall back to defaults
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "maybe")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "perhaps")

    env = ProviderEnv.from_env()
    # Defaults in from_env: offline False, lmstudio_available False
    assert env.offline is False
    assert env.lmstudio_available is False


@pytest.mark.fast
@pytest.mark.requires_resource("codebase")
def test_as_dict_reflects_values_and_with_test_defaults_sets_openai_key(monkeypatch):
    # Clean OPENAI_API_KEY to assert it is set deterministically
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    mapping = env.as_dict()
    assert mapping["DEVSYNTH_PROVIDER"] == "stub"
    assert mapping["DEVSYNTH_OFFLINE"] == "true"
    assert mapping["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "false"

    # Ensure with_test_defaults sets OPENAI_API_KEY placeholder
    ProviderEnv.from_env().with_test_defaults()
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"
