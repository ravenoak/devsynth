"""Targeted tests for provider system decision logic and helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import devsynth.adapters.provider_system as provider_system
from devsynth.adapters.provider_system import ProviderError

pytestmark = pytest.mark.fast


def _make_settings(**overrides):
    base = {
        "tls_verify": True,
        "tls_cert_file": None,
        "tls_key_file": None,
        "tls_ca_file": None,
        "provider_max_retries": 1,
        "provider_initial_delay": 0.0,
        "provider_exponential_base": 2.0,
        "provider_max_delay": 1.0,
        "provider_jitter": False,
        "provider_retry_metrics": False,
        "provider_retry_conditions": "",
        "provider_fallback_enabled": True,
        "provider_fallback_order": "openai,lmstudio",
        "provider_circuit_breaker_enabled": True,
        "provider_failure_threshold": 1,
        "provider_recovery_timeout": 1.0,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture(autouse=True)
def reset_provider_state(monkeypatch):
    """Reset cached provider config and neutralize optional clients."""

    if hasattr(provider_system.get_provider_config, "cache_clear"):
        provider_system.get_provider_config.cache_clear()

    # Optional HTTP clients should be harmless during unit tests.
    monkeypatch.setattr(provider_system, "httpx", None)

    class _RequestsStub:
        class exceptions:  # noqa: D401 - mimic requests.exceptions namespace
            RequestException = Exception

    monkeypatch.setattr(provider_system, "requests", _RequestsStub())
    yield
    if hasattr(provider_system.get_provider_config, "cache_clear"):
        provider_system.get_provider_config.cache_clear()


def _configure_settings(monkeypatch, **overrides):
    settings = _make_settings(**overrides)

    def _fake_get_settings(*args, **kwargs):
        return settings

    monkeypatch.setattr(provider_system, "get_settings", _fake_get_settings)
    if hasattr(provider_system.get_provider_config, "cache_clear"):
        provider_system.get_provider_config.cache_clear()
    return settings


def test_factory_honors_disable_flag(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.setenv("DEVSYNTH_DISABLE_PROVIDERS", "1")

    provider = provider_system.ProviderFactory.create_provider("openai")

    assert isinstance(provider, provider_system.NullProvider)
    assert provider.reason == "Disabled by DEVSYNTH_DISABLE_PROVIDERS"


def test_offline_guard_uses_stub_safe_default(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = provider_system.ProviderFactory.create_provider("openai")

    assert isinstance(provider, provider_system.StubProvider)


def test_offline_guard_uses_null_when_requested(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "true")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "null")

    provider = provider_system.ProviderFactory.create_provider("openai")

    assert isinstance(provider, provider_system.NullProvider)
    assert provider.reason == "DEVSYNTH_OFFLINE active; using safe provider"


def test_explicit_openai_without_key_returns_null(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider("openai")

    assert isinstance(provider, provider_system.NullProvider)
    assert "Missing OPENAI_API_KEY" in provider.reason


def test_lmstudio_availability_guard_returns_safe_provider(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "lmstudio")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")
    monkeypatch.delenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", raising=False)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    if hasattr(provider_system.get_provider_config, "cache_clear"):
        provider_system.get_provider_config.cache_clear()

    provider = provider_system.ProviderFactory.create_provider()

    assert isinstance(provider, provider_system.StubProvider)


def test_lmstudio_fallback_failure_promotes_safe_provider(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    class _BoomLMStudio:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("LM Studio down")

    monkeypatch.setattr(provider_system, "LMStudioProvider", _BoomLMStudio)
    if hasattr(provider_system.get_provider_config, "cache_clear"):
        provider_system.get_provider_config.cache_clear()

    provider = provider_system.ProviderFactory.create_provider()

    assert isinstance(provider, provider_system.StubProvider)


def test_explicit_anthropic_without_key_returns_null(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider("anthropic")

    assert isinstance(provider, provider_system.NullProvider)
    assert "Anthropic API key is required" in provider.reason


def test_anthropic_unsupported_error(monkeypatch):
    _configure_settings(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider("anthropic")

    assert isinstance(provider, provider_system.NullProvider)
    assert "Anthropic provider is not supported" in provider.reason


class PrimaryTestProvider:
    def __init__(self, *, error: Exception | None = None, result: str | None = None):
        self.error = error
        self.result = result
        self.calls = 0

    def complete(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class SecondaryTestProvider:
    def __init__(self, *, error: Exception | None = None, result: str | None = None):
        self.error = error
        self.result = result
        self.calls = 0

    def complete(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def _fallback_config(**overrides):
    base = {
        "retry": {
            "max_retries": 0,
            "initial_delay": 0.0,
            "exponential_base": 2.0,
            "max_delay": 0.0,
            "jitter": False,
            "track_metrics": False,
            "conditions": [],
        },
        "fallback": {"enabled": True, "order": ["primary", "secondary"]},
        "circuit_breaker": {"enabled": False},
    }
    base.update(overrides)
    return base


def test_fallback_provider_uses_next_provider_on_failure():
    primary = PrimaryTestProvider(error=ProviderError("boom"))
    secondary = SecondaryTestProvider(result="ok")
    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(),
    )

    result = fallback.complete("prompt")

    assert result == "ok"
    assert primary.calls == 1
    assert secondary.calls == 1


def test_fallback_provider_propagates_failure_when_all_fail():
    primary = PrimaryTestProvider(error=ProviderError("fail primary"))
    secondary = SecondaryTestProvider(error=ProviderError("fail secondary"))
    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(),
    )

    with pytest.raises(ProviderError) as excinfo:
        fallback.complete("prompt")

    assert "fail secondary" in str(excinfo.value)
    assert primary.calls == 1
    assert secondary.calls == 1


class FakeCircuitBreaker:
    def __init__(self, state: str = "closed"):
        self.state = state
        self.failures = 0
        self.successes = 0

    def call(self, func, **kwargs):  # pragma: no cover - sync path unused here
        if self.state != "closed":
            raise ProviderError("Circuit open")
        return func(**kwargs)

    def _record_failure(self):
        self.failures += 1
        self.state = "open"

    def _record_success(self):
        self.successes += 1
        self.state = "closed"


class AsyncPrimaryProvider:
    def __init__(self, *, result: str | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = 0

    async def acomplete(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class AsyncSecondaryProvider:
    def __init__(self, *, result: str | None = None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.calls = 0

    async def acomplete(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


@pytest.mark.asyncio
async def test_async_fallback_skips_open_circuit_breaker():
    providers = [AsyncPrimaryProvider(result="unused"), AsyncSecondaryProvider(result="good")]
    fallback = provider_system.FallbackProvider(
        providers=providers,
        config=_fallback_config(circuit_breaker={"enabled": True}),
    )
    fallback.circuit_breakers = {
        "asyncprimary": FakeCircuitBreaker(state="open"),
        "asyncsecondary": FakeCircuitBreaker(state="closed"),
    }

    result = await fallback.acomplete("prompt")

    assert result == "good"
    assert providers[0].calls == 0  # breaker prevented call
    assert providers[1].calls == 1
    assert fallback.circuit_breakers["asyncsecondary"].successes == 1


def _metrics_spy(monkeypatch):
    calls: list[str] = []

    def _inc(name: str) -> None:
        calls.append(name)

    monkeypatch.setattr(provider_system, "inc_provider", _inc)
    return calls


def test_complete_helper_increments_metrics_and_propagates_error(monkeypatch):
    calls = _metrics_spy(monkeypatch)

    class _Provider:
        def __init__(self):
            self.called = 0

        def complete(self, **kwargs):
            self.called += 1
            raise ProviderError("upstream failure")

    provider = _Provider()
    monkeypatch.setattr(provider_system, "get_provider", lambda **kwargs: provider)

    with pytest.raises(ProviderError):
        provider_system.complete("prompt")

    assert calls == ["complete"]
    assert provider.called == 1


def test_embed_helper_wraps_non_provider_errors(monkeypatch):
    calls = _metrics_spy(monkeypatch)

    class _Provider:
        def __init__(self):
            self.called = 0

        def embed(self, **kwargs):
            self.called += 1
            raise RuntimeError("boom")

    provider = _Provider()
    monkeypatch.setattr(provider_system, "get_provider", lambda **kwargs: provider)

    with pytest.raises(ProviderError) as excinfo:
        provider_system.embed(["text"])

    assert "Embedding call failed" in str(excinfo.value)
    assert calls == ["embed"]
    assert provider.called == 1


@pytest.mark.asyncio
async def test_acomplete_helper_increments_metrics(monkeypatch):
    calls = _metrics_spy(monkeypatch)

    class _Provider:
        def __init__(self):
            self.called = 0

        async def acomplete(self, **kwargs):
            self.called += 1
            return "async result"

    provider = _Provider()
    monkeypatch.setattr(provider_system, "get_provider", lambda **kwargs: provider)

    result = await provider_system.acomplete("prompt")

    assert result == "async result"
    assert calls == ["acomplete"]
    assert provider.called == 1


@pytest.mark.asyncio
async def test_aembed_helper_promotes_unexpected_errors(monkeypatch):
    calls = _metrics_spy(monkeypatch)

    class _Provider:
        def __init__(self):
            self.called = 0

        async def aembed(self, **kwargs):
            self.called += 1
            raise RuntimeError("bad async")

    provider = _Provider()
    monkeypatch.setattr(provider_system, "get_provider", lambda **kwargs: provider)

    with pytest.raises(ProviderError) as excinfo:
        await provider_system.aembed(["text"])

    assert "Embedding call failed" in str(excinfo.value)
    assert calls == ["aembed"]
    assert provider.called == 1
