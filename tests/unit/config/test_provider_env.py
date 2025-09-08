import json
import os

import pytest

from devsynth.config.provider_env import ProviderEnv, _parse_bool


@pytest.mark.fast
def test_parse_bool_truthy_and_falsy_cases():
    """ReqID: ENV-BOOL-01 — _parse_bool handles truthy/falsy/default cases."""
    # truthy
    for v in ["1", "true", "TrUe", "YES", "on", 1, True]:
        assert (
            _parse_bool(str(v) if not isinstance(v, str) else v, default=False) is True
        )
    # falsy
    for v in ["0", "false", "FaLsE", "no", "off", 0, False]:
        assert (
            _parse_bool(str(v) if not isinstance(v, str) else v, default=True) is False
        )
    # default when unknown
    assert _parse_bool("maybe", default=True) is True
    assert _parse_bool("maybe", default=False) is False
    assert _parse_bool(None, default=True) is True


@pytest.mark.fast
def test_from_env_defaults_and_with_test_defaults_sets_stub_and_offline(monkeypatch):
    """ReqID: ENV-DEFAULTS-01 — Defaults and test defaults.

    - Defaults: provider=openai, offline=false
    - with_test_defaults(): provider=stub, offline=true, placeholder OPENAI key
    """
    # Ensure clean env
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    env = ProviderEnv.from_env()
    assert env.provider == "openai"
    assert env.offline is False
    assert env.lmstudio_available is False

    test_env = env.with_test_defaults()
    # Provider should default to stub, offline to True, lmstudio False
    assert test_env.provider == "stub"
    assert test_env.offline is True
    assert test_env.lmstudio_available is False
    # OPENAI_API_KEY should be populated deterministically
    assert os.environ.get("OPENAI_API_KEY") == "test-openai-key"


@pytest.mark.fast
def test_apply_to_env_respects_existing_lmstudio_flag(monkeypatch):
    """ReqID: ENV-APPLY-01 — apply_to_env respects explicit LM Studio flag.

    It should not override DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE when already set.
    """
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    pe = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    pe.apply_to_env()
    # Provider and offline should be written
    assert os.environ["DEVSYNTH_PROVIDER"] == "stub"
    assert os.environ["DEVSYNTH_OFFLINE"] == "true"
    # Existing lmstudio flag should not be overridden
    assert os.environ["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] == "true"


@pytest.mark.fast
def test_as_dict_roundtrip_and_types():
    """ReqID: ENV-DICT-01 — as_dict returns stable, JSON-serializable mapping."""
    pe = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    d = pe.as_dict()
    assert d == {
        "DEVSYNTH_PROVIDER": "stub",
        "DEVSYNTH_OFFLINE": "true",
        "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE": "false",
    }
    # simple json-serializable
    json.dumps(d)
