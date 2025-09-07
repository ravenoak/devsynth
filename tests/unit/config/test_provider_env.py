# flake8: noqa: E501
import os

import pytest

from devsynth.config.provider_env import ProviderEnv

pytestmark = [pytest.mark.fast]


def test_from_env_defaults_is_openai_offline_false(monkeypatch):
    """ReqID: ENV-01 — default provider=openai, offline=false, lmstudio=false."""
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    env = ProviderEnv.from_env()
    assert env.provider == "openai"
    assert env.offline is False
    assert env.lmstudio_available is False


def test_parse_truthy_and_falsy_via_from_env(monkeypatch):
    """ReqID: ENV-02 — truthy/falsy parsing for OFFLINE and availability."""
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "Yes")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "0")
    env = ProviderEnv.from_env()
    assert env.offline is True
    assert env.lmstudio_available is False


def test_with_test_defaults_forces_stub_and_offline_true_and_placeholder_key(
    monkeypatch,
):
    """ReqID: ENV-03 — with_test_defaults forces stub+offline and sets placeholder key."""
    # Start clean
    for k in [
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        "OPENAI_API_KEY",
    ]:
        monkeypatch.delenv(k, raising=False)
    base = ProviderEnv.from_env()
    tweaked = base.with_test_defaults()
    assert tweaked.provider == "stub"
    assert tweaked.offline is True
    assert tweaked.lmstudio_available is False
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


def test_with_test_defaults_respects_explicit_provider_and_offline(monkeypatch):
    """ReqID: ENV-04 — explicit provider/offline respected by with_test_defaults."""
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "anthropic")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    base = ProviderEnv.from_env()
    tweaked = base.with_test_defaults()
    # Provider explicitly set should be respected
    assert tweaked.provider == "anthropic"
    # offline remains False because it was explicitly provided
    assert tweaked.offline is False


def test_apply_to_env_sets_expected_vars(monkeypatch):
    """ReqID: ENV-05 — apply_to_env sets expected variables when unset."""
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    env.apply_to_env()
    assert os.environ["DEVSYNTH_PROVIDER"] == "stub"
    assert os.environ["DEVSYNTH_OFFLINE"] == "true"
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "false"


def test_apply_to_env_does_not_override_existing_availability(monkeypatch):
    """ReqID: ENV-06 — apply_to_env preserves explicit availability value."""
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    env.apply_to_env()
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "true"


def test_as_dict_round_trip(monkeypatch):
    """ReqID: ENV-07 — as_dict produces env-style mapping."""
    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=True)
    d = env.as_dict()
    assert d == {
        "DEVSYNTH_PROVIDER": "stub",
        "DEVSYNTH_OFFLINE": "true",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "true",
    }
