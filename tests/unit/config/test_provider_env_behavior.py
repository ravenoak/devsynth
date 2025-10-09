import os

import pytest

from devsynth.config.provider_env import ProviderEnv

pytestmark = pytest.mark.fast


def test_from_env_defaults_when_unset(monkeypatch):
    """ReqID: ENV-10 — from_env defaults.

    Returns openai/online with lmstudio availability false when unset.
    """
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    env = ProviderEnv.from_env()
    assert env.provider == "openai"
    assert env.offline is False
    assert env.lmstudio_available is False


def test_with_test_defaults_overrides_to_safe_when_unset(monkeypatch):
    """ReqID: ENV-11

    Sets safe defaults: stub provider, offline=true, placeholder key.
    """
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    # Also ensure API key isn't set so with_test_defaults sets a placeholder
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    base = ProviderEnv.from_env()
    safe = base.with_test_defaults()

    assert safe.provider == "stub"
    assert safe.offline is True
    assert safe.lmstudio_available is False
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


def test_with_test_defaults_respects_explicit_provider(monkeypatch):
    """ReqID: ENV-12 — respects explicit provider and offline flag."""
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "anthropic")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "1")

    base = ProviderEnv.from_env()
    safe = base.with_test_defaults()

    # Provider explicitly set should be respected
    assert safe.provider == "anthropic"
    # Offline should default to True only if unset; here it was explicitly false
    assert safe.offline is False
    # LM Studio availability should carry through from base
    assert safe.lmstudio_available is True


def test_apply_to_env_and_as_dict_roundtrip(monkeypatch):
    """ReqID: ENV-13 — apply_to_env populates vars; as_dict round-trips mapping."""
    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    env.apply_to_env()

    assert os.environ["DEVSYNTH_PROVIDER"] == "stub"
    assert os.environ["DEVSYNTH_OFFLINE"] == "true"
    # apply_to_env sets availability only if missing; simulate missing
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    env.apply_to_env()
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "false"

    d = env.as_dict()
    assert d == {
        "DEVSYNTH_PROVIDER": "stub",
        "DEVSYNTH_OFFLINE": "true",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "false",
    }
