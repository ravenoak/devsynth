import contextlib
import importlib
import os

import pytest

from devsynth.adapters import provider_system
from devsynth.adapters.providers.provider_factory import (
    ProviderError,
    ProviderFactory,
    ProviderType,
)


@contextlib.contextmanager
def temp_env(**env):
    old = {}
    for k, v in env.items():
        old[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def reset_provider_config_cache():
    # Clear lru_cache on get_provider_config to respect env changes
    if hasattr(provider_system.get_provider_config, "cache_clear"):
        provider_system.get_provider_config.cache_clear()


def test_default_safe_falls_back_to_stub_without_keys_and_lmstudio():
    with temp_env(
        DEVSYNTH_DISABLE_PROVIDERS=None,
        DEVSYNTH_PROVIDER=None,
        OPENAI_API_KEY=None,
        ANTHROPIC_API_KEY=None,
        DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE="false",
        DEVSYNTH_SAFE_DEFAULT_PROVIDER="stub",
    ):
        reset_provider_config_cache()
        prov = ProviderFactory.create_provider()
        assert isinstance(prov, provider_system.StubProvider)


def test_openai_explicit_without_key_raises():
    with temp_env(OPENAI_API_KEY=None):
        reset_provider_config_cache()
        with pytest.raises(ProviderError):
            ProviderFactory.create_provider(ProviderType.OPENAI.value)


def test_anthropic_implicit_without_key_falls_back_safe_default_stub():
    with temp_env(
        DEVSYNTH_PROVIDER="anthropic",
        ANTHROPIC_API_KEY=None,
        DEVSYNTH_SAFE_DEFAULT_PROVIDER="stub",
    ):
        reset_provider_config_cache()
        prov = ProviderFactory.create_provider()
        assert isinstance(prov, provider_system.StubProvider)


def test_lmstudio_not_attempted_without_availability_flag():
    # Even if default provider is openai and no key, LM Studio should not be probed unless flagged
    with temp_env(
        DEVSYNTH_PROVIDER="openai",
        OPENAI_API_KEY=None,
        DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE="false",
        DEVSYNTH_SAFE_DEFAULT_PROVIDER="stub",
    ):
        reset_provider_config_cache()
        prov = ProviderFactory.create_provider()
        assert isinstance(prov, provider_system.StubProvider)


def test_disable_providers_returns_null():
    with temp_env(DEVSYNTH_DISABLE_PROVIDERS="true"):
        prov = ProviderFactory.create_provider()
        assert isinstance(prov, provider_system.NullProvider)
