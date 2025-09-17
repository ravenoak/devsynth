from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from devsynth.adapters import provider_system
from devsynth.adapters.provider_system import (
    BaseProvider,
    FallbackProvider,
    ProviderError,
)
from devsynth.security.tls import TLSConfig


def _make_retry_config() -> dict[str, object]:
    return {
        "max_retries": 1,
        "initial_delay": 0.0,
        "exponential_base": 1.0,
        "max_delay": 0.0,
        "jitter": False,
        "track_metrics": False,
        "conditions": [],
    }


class _FakeCircuitBreaker:
    def __init__(self, *_, **kwargs) -> None:
        self.failure_threshold = kwargs.get("failure_threshold")
        self.recovery_timeout = kwargs.get("recovery_timeout")
        self.state = "closed"
        self.call_records: list[tuple[str, tuple, dict]] = []
        self.failure_records = 0
        self.success_records = 0

    def call(self, func, *args, **kwargs):  # pragma: no cover - trivial passthrough
        self.call_records.append((func.__name__, args, kwargs))
        return func(*args, **kwargs)

    def _record_failure(self) -> None:
        self.failure_records += 1
        self.state = "open"

    def _record_success(self) -> None:
        self.success_records += 1
        self.state = "closed"


class FakeProvider(BaseProvider):
    def __init__(self) -> None:
        super().__init__(retry_config=_make_retry_config())
        self.should_fail_sync = False
        self.should_fail_async = False
        self.fail_exception: Exception = RuntimeError("boom")
        self.sync_calls = 0
        self.async_calls = 0

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict | None = None,
    ) -> str:
        self.sync_calls += 1
        if self.should_fail_sync:
            raise self.fail_exception
        return f"sync:{prompt}"

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict | None = None,
    ) -> str:
        self.async_calls += 1
        if self.should_fail_async:
            raise self.fail_exception
        return f"async:{prompt}"


class FakeFactory:
    def __init__(self, mapping: dict[str, FakeProvider]) -> None:
        self._mapping = mapping
        self.calls: list[str] = []

    def create_provider(self, provider_type: str, *, config, retry_config, **_kwargs):
        self.calls.append(provider_type)
        return self._mapping[provider_type]


@pytest.mark.fast
def test_provider_factory_respects_disable_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return a null provider when the disable flag is active.

    ReqID: N/A
    """
    config = {
        "default_provider": "openai",
        "openai": {"api_key": "token", "model": "gpt", "base_url": "https://api"},
        "lmstudio": {"endpoint": "http://localhost", "model": "default"},
        "retry": _make_retry_config(),
    }

    def fake_get_provider_config():
        return config

    def _no_cache() -> None:
        return None

    fake_get_provider_config.cache_clear = _no_cache  # type: ignore[attr-defined]
    monkeypatch.setattr(
        provider_system, "get_provider_config", fake_get_provider_config
    )

    fake_settings = SimpleNamespace(
        tls_verify=True,
        tls_cert_file=None,
        tls_key_file=None,
        tls_ca_file=None,
        provider_max_retries=1,
        provider_initial_delay=0.1,
        provider_exponential_base=2.0,
        provider_max_delay=1.0,
        provider_jitter=False,
        provider_retry_metrics=False,
        provider_retry_conditions="",
        provider_fallback_enabled=False,
        provider_fallback_order="openai",
        provider_circuit_breaker_enabled=False,
        provider_failure_threshold=3,
        provider_recovery_timeout=1.0,
    )
    monkeypatch.setattr(provider_system, "get_settings", lambda: fake_settings)
    monkeypatch.setenv("DEVSYNTH_DISABLE_PROVIDERS", "true")

    provider = provider_system.ProviderFactory.create_provider("openai")
    assert isinstance(provider, provider_system.NullProvider)
    assert provider.reason == "Disabled by DEVSYNTH_DISABLE_PROVIDERS"


@pytest.mark.fast
def test_tls_config_defaults_when_settings_missing() -> None:
    """Use TLS defaults when settings object lacks overrides.

    ReqID: N/A
    """
    tls = provider_system._create_tls_config(SimpleNamespace())
    assert isinstance(tls, TLSConfig)
    assert tls.verify is True
    assert tls.cert_file is None
    assert tls.key_file is None
    assert tls.ca_file is None


@pytest.mark.fast
def test_tls_config_uses_explicit_settings() -> None:
    """Honor explicit TLS overrides from settings.

    ReqID: N/A
    """
    settings = SimpleNamespace(
        tls_verify=False,
        tls_cert_file="/tmp/cert.pem",
        tls_key_file="/tmp/key.pem",
        tls_ca_file="/tmp/ca.pem",
    )
    tls = provider_system._create_tls_config(settings)
    assert tls.verify is False
    assert tls.cert_file == "/tmp/cert.pem"
    assert tls.key_file == "/tmp/key.pem"
    assert tls.ca_file == "/tmp/ca.pem"


@pytest.mark.fast
def test_retry_decorator_wiring(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure providers pass retry configuration through to the helper.

    ReqID: N/A
    """
    captured: dict[str, object] = {}

    def fake_retry_with_exponential_backoff(**kwargs):
        captured.update(kwargs)
        return "decorated"

    monkeypatch.setattr(
        provider_system,
        "retry_with_exponential_backoff",
        fake_retry_with_exponential_backoff,
    )

    class SampleProvider(BaseProvider):
        pass

    provider = SampleProvider(
        retry_config={
            "max_retries": 5,
            "initial_delay": 0.5,
            "exponential_base": 3.0,
            "max_delay": 4.0,
            "jitter": False,
            "track_metrics": False,
            "conditions": ["boom"],
        }
    )

    def always_retry(_exc: Exception) -> bool:
        return True

    decorator = provider.get_retry_decorator((RuntimeError,), should_retry=always_retry)
    assert decorator == "decorated"

    assert captured["max_retries"] == 5
    assert captured["initial_delay"] == 0.5
    assert captured["exponential_base"] == 3.0
    assert captured["max_delay"] == 4.0
    assert captured["jitter"] is False
    assert captured["retry_conditions"] == ["boom"]
    assert captured["track_metrics"] is False
    assert captured["retryable_exceptions"] == (RuntimeError,)
    assert captured["should_retry"] is always_retry
    assert captured["on_retry"] == provider._emit_retry_telemetry


@pytest.mark.fast
def test_fallback_provider_sync_uses_circuit_breaker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Route sync calls through the configured circuit breaker.

    ReqID: N/A
    """
    monkeypatch.setattr(provider_system, "CircuitBreaker", _FakeCircuitBreaker)
    provider = FakeProvider()
    factory = FakeFactory({"fake": provider})
    config = {
        "fallback": {"enabled": True, "order": ["fake"]},
        "retry": _make_retry_config(),
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 1,
            "recovery_timeout": 0,
        },
    }

    fallback = FallbackProvider(config=config, provider_factory=factory)
    result = fallback.complete("prompt")
    assert result == "sync:prompt"
    breaker = fallback.circuit_breakers["fake"]
    assert breaker.call_records
    assert provider.sync_calls == 1


@pytest.mark.fast
def test_fallback_provider_async_failure_opens_breaker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise ProviderError and open the breaker after async failures.

    ReqID: N/A
    """
    monkeypatch.setattr(provider_system, "CircuitBreaker", _FakeCircuitBreaker)
    provider = FakeProvider()
    provider.should_fail_async = True
    factory = FakeFactory({"fake": provider})
    config = {
        "fallback": {"enabled": True, "order": ["fake"]},
        "retry": _make_retry_config(),
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 1,
            "recovery_timeout": 0,
        },
    }
    fallback = FallbackProvider(config=config, provider_factory=factory)

    async def run() -> None:
        with pytest.raises(ProviderError) as excinfo:
            await fallback.acomplete("prompt")
        assert "Provider FakeProvider failed" in str(excinfo.value)

    asyncio.run(run())
    breaker = fallback.circuit_breakers["fake"]
    assert breaker.failure_records == 1
    assert breaker.state == "open"
    assert provider.async_calls == 1


@pytest.mark.fast
def test_fallback_provider_async_respects_open_breaker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refuse async calls when the circuit breaker is open.

    ReqID: N/A
    """
    monkeypatch.setattr(provider_system, "CircuitBreaker", _FakeCircuitBreaker)
    provider = FakeProvider()
    factory = FakeFactory({"fake": provider})
    config = {
        "fallback": {"enabled": True, "order": ["fake"]},
        "retry": _make_retry_config(),
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 1,
            "recovery_timeout": 0,
        },
    }
    fallback = FallbackProvider(config=config, provider_factory=factory)
    fallback.circuit_breakers["fake"].state = "open"

    async def run() -> None:
        with pytest.raises(ProviderError) as excinfo:
            await fallback.acomplete("prompt")
        assert "circuit breaker is open" in str(excinfo.value)

    asyncio.run(run())
    assert provider.async_calls == 0


@pytest.mark.fast
def test_fallback_provider_async_records_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Record success metrics and reset breaker after async success.

    ReqID: N/A
    """
    monkeypatch.setattr(provider_system, "CircuitBreaker", _FakeCircuitBreaker)
    provider = FakeProvider()
    factory = FakeFactory({"fake": provider})
    config = {
        "fallback": {"enabled": True, "order": ["fake"]},
        "retry": _make_retry_config(),
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 1,
            "recovery_timeout": 0,
        },
    }
    fallback = FallbackProvider(config=config, provider_factory=factory)

    async def run() -> None:
        result = await fallback.acomplete("prompt")
        assert result == "async:prompt"

    asyncio.run(run())
    breaker = fallback.circuit_breakers["fake"]
    assert breaker.success_records == 1
    assert breaker.state == "closed"
    assert provider.async_calls == 1


@pytest.mark.fast
def test_complete_failure_increments_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """Count metric events when completions raise provider errors.

    ReqID: N/A
    """
    provider = MagicMock()
    provider.complete.side_effect = ProviderError("fail")
    monkeypatch.setattr(
        provider_system,
        "get_provider",
        lambda provider_type=None, fallback=False: provider,
    )
    metrics = MagicMock()
    monkeypatch.setattr(provider_system, "inc_provider", metrics)

    with pytest.raises(ProviderError):
        provider_system.complete("prompt", provider_type="openai", fallback=False)

    metrics.assert_called_once_with("complete")


@pytest.mark.fast
def test_embed_wraps_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wrap non-provider exceptions raised by embed implementations.

    ReqID: N/A
    """
    provider = MagicMock()
    provider.embed.side_effect = ValueError("boom")
    monkeypatch.setattr(
        provider_system,
        "get_provider",
        lambda provider_type=None, fallback=False: provider,
    )
    metrics = MagicMock()
    monkeypatch.setattr(provider_system, "inc_provider", metrics)

    with pytest.raises(ProviderError) as excinfo:
        provider_system.embed("text", provider_type="lmstudio", fallback=False)

    assert "Embedding call failed: boom" in str(excinfo.value)
    metrics.assert_called_once_with("embed")


@pytest.mark.fast
def test_acomplete_failure_increments_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure async completions increment metrics on failure.

    ReqID: N/A
    """
    provider = MagicMock()
    provider.acomplete = AsyncMock(side_effect=ProviderError("boom"))
    monkeypatch.setattr(
        provider_system,
        "get_provider",
        lambda provider_type=None, fallback=False: provider,
    )
    metrics = MagicMock()
    monkeypatch.setattr(provider_system, "inc_provider", metrics)

    async def run() -> None:
        with pytest.raises(ProviderError):
            await provider_system.acomplete(
                "prompt", provider_type="openai", fallback=False
            )

    asyncio.run(run())
    metrics.assert_called_once_with("acomplete")


@pytest.mark.fast
def test_aembed_wraps_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Convert unexpected async embedding errors into ProviderError.

    ReqID: N/A
    """
    provider = MagicMock()
    provider.aembed = AsyncMock(side_effect=ValueError("boom"))
    monkeypatch.setattr(
        provider_system,
        "get_provider",
        lambda provider_type=None, fallback=False: provider,
    )
    metrics = MagicMock()
    monkeypatch.setattr(provider_system, "inc_provider", metrics)

    async def run() -> None:
        with pytest.raises(ProviderError) as excinfo:
            await provider_system.aembed(
                "text", provider_type="lmstudio", fallback=False
            )
        assert "Embedding call failed: boom" in str(excinfo.value)

    asyncio.run(run())
    metrics.assert_called_once_with("aembed")
