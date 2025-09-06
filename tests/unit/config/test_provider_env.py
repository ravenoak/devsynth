import os
import pytest

from devsynth.config.provider_env import ProviderEnv


@pytest.mark.fast
def test_with_test_defaults_applies_stub_offline_and_placeholder_key(monkeypatch):
    # Start from a clean environment relevant to provider settings
    for k in [
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        "OPENAI_API_KEY",
    ]:
        monkeypatch.delenv(k, raising=False)

    base = ProviderEnv.from_env()
    assert base.provider == "openai"
    assert base.offline is False
    assert base.lmstudio_available is False

    pe = base.with_test_defaults()
    assert pe.provider == "stub"  # defaults to stub when not explicitly set
    assert pe.offline is True      # defaults to offline=True for tests
    assert pe.lmstudio_available is False
    # Placeholder API key is set deterministically
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


@pytest.mark.fast
def test_with_test_defaults_respects_explicit_provider_and_offline_false(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    base = ProviderEnv.from_env()
    assert base.provider == "openai"
    assert base.offline is False

    pe = base.with_test_defaults()
    # Explicit provider is respected when already set
    assert pe.provider == "openai"
    # Since DEVSYNTH_OFFLINE exists and is false, offline should remain False
    assert pe.offline is False
    # Placeholder key still set to ensure deterministic offline behavior
    assert os.environ["OPENAI_API_KEY"] == "test-openai-key"


@pytest.mark.fast
def test_apply_to_env_sets_expected_variables_when_unset(monkeypatch):
    # Compose a ProviderEnv and apply it to an empty env; ensure correct values
    for k in [
        "DEVSYNTH_PROVIDER",
        "DEVSYNTH_OFFLINE",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
    ]:
        monkeypatch.delenv(k, raising=False)

    pe = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    pe.apply_to_env()

    assert os.environ["DEVSYNTH_PROVIDER"] == "stub"
    assert os.environ["DEVSYNTH_OFFLINE"] == "true"
    # Availability is written when previously unset
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "false"


@pytest.mark.fast
def test_apply_to_env_does_not_override_explicit_availability(monkeypatch):
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")

    pe = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    pe.apply_to_env()

    # Explicit user choice is preserved
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "true"


@pytest.mark.fast
def test_as_dict_round_trip(monkeypatch):
    pe = ProviderEnv(provider="openai", offline=False, lmstudio_available=True)
    d = pe.as_dict()
    assert d == {
        "DEVSYNTH_PROVIDER": "openai",
        "DEVSYNTH_OFFLINE": "false",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "true",
    }

    # Simulate applying and reading back
    monkeypatch.setenv("DEVSYNTH_PROVIDER", d["DEVSYNTH_PROVIDER"])
    monkeypatch.setenv("DEVSYNTH_OFFLINE", d["DEVSYNTH_OFFLINE"])
    monkeypatch.setenv(
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
        d["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"],
    )

    round_trip = ProviderEnv.from_env()
    assert round_trip.provider == "openai"
    assert round_trip.offline is False
    assert round_trip.lmstudio_available is True


@pytest.mark.fast
def test_explicit_provider_without_keys_has_no_side_effect_errors(monkeypatch):
    # Ensure that setting a real provider but no API key does not raise when using test defaults
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    pe = ProviderEnv.from_env().with_test_defaults()
    # Should set placeholder key to avoid accidental network usage
    assert os.environ["OPENAI_API_KEY"] == "test-openai-key"
    # No exceptions expected and provider remains openai
    assert pe.provider == "openai"