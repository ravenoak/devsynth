"""Additional coverage for :mod:`devsynth.adapters.provider_system`."""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.fast


@pytest.fixture()
def provider_module(monkeypatch: pytest.MonkeyPatch):
    """Reload provider system with deterministic settings and clean cache."""

    import devsynth.adapters.provider_system as provider_system

    module = importlib.reload(provider_system)

    settings = SimpleNamespace(
        tls_verify=True,
        tls_cert_file=None,
        tls_key_file=None,
        tls_ca_file=None,
        provider_max_retries=1,
        provider_initial_delay=0.1,
        provider_exponential_base=2.0,
        provider_max_delay=1.0,
        provider_jitter=False,
        provider_retry_metrics=True,
        provider_retry_conditions="",
        provider_fallback_enabled=True,
        provider_fallback_order="stub",
        provider_circuit_breaker_enabled=False,
        provider_failure_threshold=1,
        provider_recovery_timeout=1.0,
    )

    monkeypatch.setattr(module, "get_settings", lambda *_, **__: settings)
    if hasattr(module.get_provider_config, "cache_clear"):
        module.get_provider_config.cache_clear()

    yield module

    if hasattr(module.get_provider_config, "cache_clear"):
        module.get_provider_config.cache_clear()


def test_offline_mode_uses_safe_provider(provider_module, monkeypatch):
    """When offline mode is active a stub provider is returned.

    ReqID: coverage-provider-system
    """

    module = provider_module
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = module.ProviderFactory.create_provider("openai")
    assert isinstance(provider, module.StubProvider)


def test_offline_mode_null_provider(provider_module, monkeypatch):
    """Switching the safe provider flag returns a null provider with reason.

    ReqID: coverage-provider-system
    """

    module = provider_module
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "1")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "null")

    provider = module.ProviderFactory.create_provider("openai")
    assert isinstance(provider, module.NullProvider)
    assert "DEVSYNTH_OFFLINE" in provider.reason


def test_unknown_provider_falls_back(provider_module, monkeypatch):
    """Unknown provider identifiers fall back to configured safe provider.

    ReqID: coverage-provider-system
    """

    module = provider_module
    monkeypatch.delenv("DEVSYNTH_OFFLINE", raising=False)
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")

    provider = module.ProviderFactory.create_provider("does-not-exist")
    assert isinstance(provider, module.StubProvider)


def test_retry_decorator_uses_provider_config(monkeypatch, provider_module):
    """Retry helper forwards provider configuration to backoff utility.

    ReqID: coverage-provider-system
    """

    module = provider_module
    captured = {}

    def fake_retry(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

        def decorator(func):  # noqa: ANN001
            return func

        return decorator

    monkeypatch.setattr(module, "retry_with_exponential_backoff", fake_retry)

    base = module.BaseProvider()
    decorator = base.get_retry_decorator()
    assert callable(decorator)
    assert captured["max_retries"] == 1
    assert captured["initial_delay"] == 0.1
    assert captured["exponential_base"] == 2.0


def test_stub_provider_deterministic_embeddings(provider_module):
    """Stub provider deterministic hashing returns floats in [0, 1).

    ReqID: coverage-provider-system
    """

    module = provider_module
    stub = module.StubProvider()
    values = stub.embed("hello world")
    assert len(values) == 1
    assert all(0 <= number < 1 for number in values[0])
