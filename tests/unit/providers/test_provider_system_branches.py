"""Targeted tests for provider system decision logic and helpers."""

from __future__ import annotations

import asyncio
import importlib
from types import SimpleNamespace
from typing import Any

import pytest

import devsynth.adapters.provider_system as provider_system
import devsynth.fallback as fallback_module

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


@pytest.fixture(autouse=True)
def resume_coverage():
    """Ensure coverage collection restarts after global isolation teardown."""

    try:  # pragma: no cover - defensive guard for non-coverage runs
        import coverage
    except Exception:  # pragma: no cover - coverage always available in CI
        yield
        return

    cov = coverage.Coverage.current()
    if cov is None:
        yield
        return

    try:  # pragma: no branch - start() idempotence handled by CoverageException
        cov.start()
    except Exception:  # pragma: no cover - ignore double-start edge cases
        pass
    yield


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


def _retry_config(**overrides):
    config = {
        "max_retries": 0,
        "initial_delay": 0.0,
        "exponential_base": 2.0,
        "max_delay": 1.0,
        "jitter": False,
        "track_metrics": False,
        "conditions": [],
    }
    config.update(overrides)
    return config


def _enable_real_providers(monkeypatch: pytest.MonkeyPatch):
    """Load a fresh provider_system module with real provider classes."""

    import sys
    from types import ModuleType, SimpleNamespace

    # Create a mock settings module to avoid circular import issues during reload
    mock_settings = ModuleType("devsynth.config.settings")
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

    def mock_get_settings(*_, **__):
        return settings

    mock_settings.get_settings = mock_get_settings

    # Replace the settings module in sys.modules before reload
    original_settings = sys.modules.get("devsynth.config.settings")
    sys.modules["devsynth.config.settings"] = mock_settings

    try:
        monkeypatch.setenv("DEVSYNTH_TEST_ALLOW_PROVIDERS", "true")
        module = importlib.reload(provider_system)

        if hasattr(module.get_provider_config, "cache_clear"):
            module.get_provider_config.cache_clear()
        return module
    finally:
        # Restore original settings module
        if original_settings is not None:
            sys.modules["devsynth.config.settings"] = original_settings


def test_fallback_provider_uses_next_provider_on_failure():
    primary = PrimaryTestProvider(error=provider_system.ProviderError("boom"))
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
    primary = PrimaryTestProvider(error=provider_system.ProviderError("fail primary"))
    secondary = SecondaryTestProvider(
        error=provider_system.ProviderError("fail secondary")
    )
    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(),
    )

    with pytest.raises(provider_system.ProviderError) as excinfo:
        fallback.complete("prompt")

    assert "fail secondary" in str(excinfo.value)
    assert primary.calls == 1
    assert secondary.calls == 1


def test_fallback_disabled_tries_only_first_provider():
    primary = PrimaryTestProvider(error=provider_system.ProviderError("nope"))
    secondary = SecondaryTestProvider(result="unused")
    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(fallback={"enabled": False}),
    )

    with pytest.raises(provider_system.ProviderError):
        fallback.complete("prompt")

    assert primary.calls == 1
    assert secondary.calls == 0


def test_fallback_initialization_orders_providers_and_records_circuit_results(
    monkeypatch,
):
    config = _fallback_config(
        fallback={"enabled": True, "order": ["primary", "secondary"]},
        circuit_breaker={
            "enabled": True,
            "failure_threshold": 2,
            "recovery_timeout": 9.0,
        },
    )
    config["retry"].update(
        {"max_retries": 2, "initial_delay": 0.3, "track_metrics": True}
    )

    class RecordingCircuitBreaker:
        def __init__(self, *, failure_threshold: int, recovery_timeout: float):
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.state = "closed"
            self.calls: list[dict[str, Any]] = []
            self.failures = 0
            self.successes = 0

        def call(self, func, **kwargs):
            self.calls.append(kwargs)
            try:
                result = func(**kwargs)
            except Exception:
                self._record_failure()
                raise
            else:
                self._record_success()
                return result

        def _record_failure(self):
            self.failures += 1
            self.state = "open"

        def _record_success(self):
            self.successes += 1
            self.state = "closed"

    monkeypatch.setattr(provider_system, "CircuitBreaker", RecordingCircuitBreaker)

    class Factory:
        def __init__(self):
            self.requested: list[str] = []
            self.instances: dict[str, Any] = {}
            self.retry_configs: dict[str, dict[str, Any] | None] = {}

        def create_provider(self, provider_type, **kwargs):
            self.requested.append(provider_type)
            self.retry_configs[provider_type] = kwargs.get("retry_config")

            fail = provider_type == "primary"
            result = f"{provider_type}-result"

            class _Provider:
                def __init__(self):
                    self.calls = 0

                def complete(self, **call_kwargs):
                    self.calls += 1
                    if fail:
                        raise provider_system.ProviderError(f"{provider_type} failure")
                    return result

            _Provider.__name__ = f"{provider_type.title()}Provider"
            instance = _Provider()
            self.instances[provider_type] = instance
            return instance

    factory = Factory()
    fallback = provider_system.FallbackProvider(
        config=config,
        provider_factory=factory,
    )

    assert factory.requested == ["primary", "secondary"]
    assert list(fallback.circuit_breakers) == ["primary", "secondary"]
    assert fallback.retry_config["max_retries"] == 2
    assert factory.retry_configs["primary"]["max_retries"] == 2

    result = fallback.complete("prompt")

    assert result == "secondary-result"
    assert factory.instances["primary"].calls == 1
    assert factory.instances["secondary"].calls == 1
    assert fallback.circuit_breakers["primary"].failures == 1
    assert fallback.circuit_breakers["primary"].state == "open"
    assert fallback.circuit_breakers["secondary"].successes == 1
    assert fallback.circuit_breakers["secondary"].state == "closed"


class FakeCircuitBreaker:
    def __init__(self, state: str = "closed", label: str = "provider.acomplete"):
        self._state = state
        self.failures = 0
        self.successes = 0
        self.label = label

    @property
    def state(self) -> str:
        if self._state != "closed":
            fallback_module.inc_circuit_breaker_state(self.label, self._state.upper())
        return self._state

    @state.setter
    def state(self, value: str) -> None:
        self._state = value

    def call(self, func, **kwargs):  # pragma: no cover - sync path unused here
        if self.state != "closed":
            raise provider_system.ProviderError("Circuit open")
        return func(**kwargs)

    def _record_failure(self):
        self.failures += 1
        self.state = "open"
        fallback_module.inc_circuit_breaker_state(self.label, "OPEN")

    def _record_success(self):
        self.successes += 1
        self.state = "closed"
        fallback_module.inc_circuit_breaker_state(self.label, "CLOSED")

    def reset(self) -> None:
        if self._state != "closed":
            fallback_module.inc_circuit_breaker_state(self.label, "CLOSED")
        self._state = "closed"


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
async def test_async_fallback_skips_open_circuit_breaker(monkeypatch):
    circuit_metrics = _circuit_metrics_spy(monkeypatch)
    providers = [
        AsyncPrimaryProvider(result="unused"),
        AsyncSecondaryProvider(result="good"),
    ]
    fallback = provider_system.FallbackProvider(
        providers=providers,
        config=_fallback_config(circuit_breaker={"enabled": True}),
    )
    fallback.circuit_breakers = {
        "asyncprimary": FakeCircuitBreaker(
            state="open", label="asyncprimary.acomplete"
        ),
        "asyncsecondary": FakeCircuitBreaker(
            state="closed", label="asyncsecondary.acomplete"
        ),
    }

    result = await fallback.acomplete("prompt")

    assert result == "good"
    assert providers[0].calls == 0  # breaker prevented call
    assert providers[1].calls == 1
    assert fallback.circuit_breakers["asyncsecondary"].successes == 1
    assert circuit_metrics == [
        ("asyncprimary.acomplete", "OPEN"),
        ("asyncsecondary.acomplete", "CLOSED"),
    ]


@pytest.mark.asyncio
async def test_openai_async_retry_emits_telemetry(monkeypatch):
    _enable_real_providers(monkeypatch)
    metrics = _metrics_spy(monkeypatch)

    class _HTTPError(Exception):
        def __init__(self, message: str, response: Any | None = None) -> None:
            super().__init__(message)
            self.response = response

    class _AsyncResponse:
        def __init__(self, data: dict[str, Any]):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    attempts: list[dict[str, Any]] = []

    class _AsyncClient:
        def __init__(self, **kwargs: Any):
            self.kwargs = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001 - stub
            attempts.append({"url": url, "json": json})
            if len(attempts) == 1:
                response = SimpleNamespace(status_code=429)
                raise _HTTPError("too many requests", response=response)
            return _AsyncResponse({"choices": [{"message": {"content": "async-ok"}}]})

    class _HttpxStub:
        HTTPError = _HTTPError

        def __init__(self):
            self.AsyncClient = _AsyncClient

    monkeypatch.setattr(provider_system, "httpx", _HttpxStub())

    recorded_delays: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        recorded_delays.append(delay)

    monkeypatch.setattr(provider_system.asyncio, "sleep", _fake_sleep)

    import random

    monkeypatch.setattr(random, "random", lambda: 0.25)

    provider = provider_system.OpenAIProvider(
        api_key="key",
        model="gpt-test",
        base_url="https://api.mock",
        retry_config=_retry_config(
            max_retries=1,
            initial_delay=0.1,
            jitter=True,
            track_metrics=True,
        ),
        tls_config=provider_system.TLSConfig(timeout=0.0),
    )

    assert provider.__class__.__name__ == "OpenAIProvider"

    result = await provider.acomplete("prompt")

    assert result == "async-ok"
    assert metrics == ["retry"]
    assert recorded_delays == pytest.approx([0.075])
    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_async_fallback_circuit_breaker_recovery(monkeypatch):
    metrics = _metrics_spy(monkeypatch)
    circuit_metrics = _circuit_metrics_spy(monkeypatch)

    class _RecordingBreaker:
        def __init__(
            self,
            failure_threshold: int,
            recovery_timeout: float,
            *_,
            label: str,
            **__,
        ):
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.state = "closed"
            self.failures = 0
            self.successes = 0
            self.label = label

        def call(self, func, **kwargs):  # noqa: ANN001 - stub
            if self.state != "closed":
                fallback_module.inc_circuit_breaker_state(
                    self.label, self.state.upper()
                )
                raise provider_system.ProviderError("Circuit open")
            return func(**kwargs)

        def _record_failure(self):
            self.failures += 1
            self.state = "open"
            fallback_module.inc_circuit_breaker_state(self.label, "OPEN")

        def _record_success(self):
            self.successes += 1
            self.state = "closed"
            fallback_module.inc_circuit_breaker_state(self.label, "CLOSED")

        def reset(self):
            self.state = "closed"
            fallback_module.inc_circuit_breaker_state(self.label, "CLOSED")

    monkeypatch.setattr(provider_system, "CircuitBreaker", _RecordingBreaker)

    class _PrimaryAsync:
        def __init__(self):
            self.calls = 0
            self.fail_next = True

        async def acomplete(self, **kwargs):
            self.calls += 1
            if self.fail_next:
                self.fail_next = False
                raise provider_system.ProviderError("429 Too Many Requests")
            return "primary-ok"

    class _SecondaryAsync:
        def __init__(self):
            self.calls = 0

        async def acomplete(self, **kwargs):
            self.calls += 1
            return "secondary-ok"

    _PrimaryAsync.__name__ = "PrimaryProvider"
    _SecondaryAsync.__name__ = "SecondaryProvider"

    primary = _PrimaryAsync()
    secondary = _SecondaryAsync()
    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(
            circuit_breaker={
                "enabled": True,
                "failure_threshold": 1,
                "recovery_timeout": 0.0,
            }
        ),
    )

    fallback.circuit_breakers = {
        "primary": _RecordingBreaker(1, 0.0, label="primary.acomplete"),
        "secondary": _RecordingBreaker(1, 0.0, label="secondary.acomplete"),
    }

    monkeypatch.setattr(provider_system, "get_provider", lambda *_, **__: fallback)

    first_result = await provider_system.acomplete("prompt")

    assert first_result == "secondary-ok"
    assert metrics == ["acomplete"]
    assert primary.calls == 1
    assert secondary.calls == 1
    primary_breaker = fallback.circuit_breakers["primary"]
    assert primary_breaker.failures == 1
    assert primary_breaker.state == "open"

    primary_breaker.reset()

    second_result = await provider_system.acomplete("prompt")

    assert second_result == "primary-ok"
    assert metrics == ["acomplete", "acomplete"]
    assert primary.calls == 2
    assert secondary.calls == 1
    assert primary_breaker.successes == 1
    assert primary_breaker.state == "closed"
    assert circuit_metrics == [
        ("primary.acomplete", "OPEN"),
        ("secondary.acomplete", "CLOSED"),
        ("primary.acomplete", "CLOSED"),
        ("primary.acomplete", "CLOSED"),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("primary_success", "secondary_success", "expected"),
    [
        (True, False, "primary-ok"),
        (False, True, "secondary-ok"),
        (False, False, None),
    ],
    ids=["primary-success", "secondary-success", "all-fail"],
)
async def test_async_fallback_metrics_permutations(
    monkeypatch, primary_success: bool, secondary_success: bool, expected: str | None
):
    metrics = _metrics_spy(monkeypatch)
    circuit_metrics = _circuit_metrics_spy(monkeypatch)

    class _RecordingBreaker:
        def __init__(
            self,
            failure_threshold: int,
            recovery_timeout: float,
            *_,
            label: str,
            **__,
        ):
            self.state = "closed"
            self.failures = 0
            self.successes = 0
            self.label = label

        def call(self, func, **kwargs):  # noqa: ANN001 - stub
            if self.state != "closed":
                fallback_module.inc_circuit_breaker_state(
                    self.label, self.state.upper()
                )
                raise provider_system.ProviderError("Circuit open")
            return func(**kwargs)

        def _record_failure(self):
            self.failures += 1
            self.state = "open"
            fallback_module.inc_circuit_breaker_state(self.label, "OPEN")

        def _record_success(self):
            self.successes += 1
            self.state = "closed"
            fallback_module.inc_circuit_breaker_state(self.label, "CLOSED")

    monkeypatch.setattr(provider_system, "CircuitBreaker", _RecordingBreaker)

    def _make_async_provider(name: str, succeed: bool):
        class _Provider:
            def __init__(self):
                self.calls = 0

            async def acomplete(self, **kwargs):
                self.calls += 1
                if not succeed:
                    message = (
                        "429 Too Many Requests"
                        if name == "primary"
                        else f"{name} failure"
                    )
                    raise provider_system.ProviderError(message)
                return f"{name}-ok"

        _Provider.__name__ = f"{name.title()}Provider"
        return _Provider()

    primary = _make_async_provider("primary", primary_success)
    secondary = _make_async_provider("secondary", secondary_success)
    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(
            circuit_breaker={
                "enabled": True,
                "failure_threshold": 1,
                "recovery_timeout": 0.0,
            }
        ),
    )

    fallback.circuit_breakers = {
        "primary": _RecordingBreaker(1, 0.0, label="primary.acomplete"),
        "secondary": _RecordingBreaker(1, 0.0, label="secondary.acomplete"),
    }

    monkeypatch.setattr(provider_system, "get_provider", lambda *_, **__: fallback)

    if expected is None:
        with pytest.raises(provider_system.ProviderError) as excinfo:
            await provider_system.acomplete("prompt")
        assert "All providers failed" in str(excinfo.value)
    else:
        result = await provider_system.acomplete("prompt")
        assert result == expected

    assert metrics == ["acomplete"]
    assert primary.calls == 1
    assert secondary.calls == (0 if primary_success else 1)

    primary_breaker = fallback.circuit_breakers["primary"]
    if primary_success:
        assert primary_breaker.successes == 1
        assert primary_breaker.failures == 0
    else:
        assert primary_breaker.failures == 1

    secondary_breaker = fallback.circuit_breakers["secondary"]
    if not primary_success and secondary_success:
        assert secondary_breaker.successes == 1
    elif not primary_success and not secondary_success:
        assert secondary_breaker.failures == 1

    if primary_success:
        expected_circuit_metrics = [("primary.acomplete", "CLOSED")]
    elif secondary_success:
        expected_circuit_metrics = [
            ("primary.acomplete", "OPEN"),
            ("secondary.acomplete", "CLOSED"),
        ]
    else:
        expected_circuit_metrics = [
            ("primary.acomplete", "OPEN"),
            ("secondary.acomplete", "OPEN"),
        ]

    assert circuit_metrics == expected_circuit_metrics


def _metrics_spy(monkeypatch):
    calls: list[str] = []

    def _inc(name: str) -> None:
        calls.append(name)

    monkeypatch.setattr(provider_system, "inc_provider", _inc)
    return calls


def _circuit_metrics_spy(monkeypatch):
    calls: list[tuple[str, str]] = []

    def _inc(name: str, state: str) -> None:
        calls.append((name, state))

    monkeypatch.setattr(fallback_module, "inc_circuit_breaker_state", _inc)
    return calls


def test_factory_applies_tls_and_retry_settings(monkeypatch):
    _configure_settings(
        monkeypatch,
        tls_verify=False,
        tls_cert_file="cert.pem",
        tls_key_file="key.pem",
        tls_ca_file="ca.pem",
        provider_retry_metrics=True,
        provider_retry_conditions="status:429,TimeoutError",
        provider_max_retries=4,
        provider_initial_delay=0.5,
    )

    provider = provider_system.ProviderFactory.create_provider("stub")

    assert isinstance(provider, provider_system.StubProvider)
    assert provider.tls_config.verify is False
    assert provider.tls_config.cert_file == "cert.pem"
    assert provider.tls_config.key_file == "key.pem"
    assert provider.tls_config.ca_file == "ca.pem"
    assert provider.retry_config["max_retries"] == 4
    assert provider.retry_config["initial_delay"] == 0.5
    assert provider.retry_config["track_metrics"] is True
    assert provider.retry_config["conditions"] == ["status:429", "TimeoutError"]


def test_emit_retry_telemetry_logs_and_counts(monkeypatch, caplog):
    base = provider_system.BaseProvider(
        retry_config={
            "max_retries": 1,
            "initial_delay": 0.1,
            "exponential_base": 2.0,
            "max_delay": 1.0,
            "jitter": False,
            "track_metrics": True,
            "conditions": [],
        }
    )
    calls = _metrics_spy(monkeypatch)

    with caplog.at_level("WARNING"):
        base._emit_retry_telemetry(RuntimeError("boom"), attempt=2, delay=0.25)

    assert calls == ["retry"]
    assert "Retrying BaseProvider" in caplog.text


def test_openai_provider_complete_builds_payload(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def post(self, url, headers, json, timeout, **kwargs):
            self.calls.append(
                {
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "timeout": timeout,
                    "kwargs": kwargs,
                }
            )

            class _Response:
                def raise_for_status(self_inner):  # noqa: ANN001 - stub
                    return None

                def json(self_inner):  # noqa: ANN001 - stub
                    return {"choices": [{"message": {"content": "answer"}}]}

            return _Response()

    requests_stub = _RequestsStub()
    monkeypatch.setattr(provider_system, "requests", requests_stub)

    provider = provider_system.OpenAIProvider(
        api_key="key",
        model="gpt-4",
        base_url="https://api.mock",
        tls_config=provider_system.TLSConfig(verify=False, timeout=2.5),
        retry_config=_retry_config(track_metrics=True),
    )

    params = {
        "messages": [
            {"role": "system", "content": "primed"},
            {"role": "user", "content": "prompt"},
        ],
        "temperature": 0.5,
        "max_tokens": 16,
        "top_p": 0.9,
        "stop": ["!"],
    }

    result = provider.complete("ignored", system_prompt="unused", parameters=params)

    assert result == "answer"
    assert requests_stub.calls, "OpenAI provider should invoke requests.post"
    call = requests_stub.calls[0]
    assert call["url"].endswith("/chat/completions")
    assert call["json"]["messages"][0]["content"] == "primed"
    assert call["json"]["stop"] == ["!"]
    assert call["timeout"] == 2.5
    assert call["kwargs"]["verify"] is False


def test_openai_provider_rejects_invalid_temperature(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

    monkeypatch.setattr(provider_system, "requests", _RequestsStub())

    provider = provider_system.OpenAIProvider(
        api_key="key",
        tls_config=provider_system.TLSConfig(),
        retry_config=_retry_config(),
    )

    with pytest.raises(provider_system.ProviderError):
        provider.complete("prompt", parameters={"temperature": 3.0})


def test_openai_provider_embed_returns_embeddings(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def post(self, url, headers, json, timeout, **kwargs):
            self.calls.append(
                {
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "timeout": timeout,
                    "kwargs": kwargs,
                }
            )

            class _Response:
                def raise_for_status(self_inner):  # noqa: ANN001 - stub
                    return None

                def json(self_inner):  # noqa: ANN001 - stub
                    return {
                        "data": [
                            {"embedding": [1.0, 0.0]},
                            {"embedding": [0.5, 0.5]},
                        ]
                    }

            return _Response()

    requests_stub = _RequestsStub()
    monkeypatch.setattr(provider_system, "requests", requests_stub)

    provider = provider_system.OpenAIProvider(
        api_key="key",
        tls_config=provider_system.TLSConfig(verify=True, timeout=1.5),
        retry_config=_retry_config(),
    )

    embeddings = provider.embed(["alpha", "beta"])

    assert embeddings == [[1.0, 0.0], [0.5, 0.5]]
    assert requests_stub.calls[0]["json"]["input"] == ["alpha", "beta"]


def test_lmstudio_provider_complete_uses_custom_messages(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def get(self, url, *args, **kwargs):
            timeout = kwargs.pop("timeout", None)
            if args:
                timeout = args[0]
            self.calls.append(
                {
                    "method": "get",
                    "url": url,
                    "timeout": timeout,
                    "kwargs": kwargs,
                }
            )

            class _Response:
                def raise_for_status(self_inner):  # noqa: ANN001 - stub
                    return None

            return _Response()

        def post(self, url, headers, json, timeout, **kwargs):
            self.calls.append(
                {
                    "method": "post",
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "timeout": timeout,
                    "kwargs": kwargs,
                }
            )

            class _Response:
                def raise_for_status(self_inner):  # noqa: ANN001 - stub
                    return None

                def json(self_inner):  # noqa: ANN001 - stub
                    return {"choices": [{"message": {"content": "lm answer"}}]}

            return _Response()

    requests_stub = _RequestsStub()
    monkeypatch.setattr(provider_system, "requests", requests_stub)

    class _TLSKwargs(dict):
        def __init__(self, verify: bool, timeout_val: float):
            super().__init__({"verify": verify})
            self._timeout = timeout_val

        def pop(self, key, default=None):  # noqa: ANN001 - behave like dict pop
            if key == "timeout":
                return self._timeout
            return super().pop(key, default)

    monkeypatch.setattr(
        provider_system.TLSConfig,
        "as_requests_kwargs",
        lambda self: _TLSKwargs(self.verify, self.timeout or 1.0),
    )

    provider = provider_system.LMStudioProvider(
        endpoint="http://localhost:1234",
        model="stub-model",
        tls_config=provider_system.TLSConfig(verify=True, timeout=1.0),
        retry_config=_retry_config(),
    )

    params = {
        "messages": [{"role": "assistant", "content": "prefill"}],
        "temperature": 0.4,
        "max_tokens": 8,
        "stop": ["###"],
    }

    result = provider.complete("prompt", system_prompt="system", parameters=params)

    assert result == "lm answer"
    post_call = next(
        call for call in requests_stub.calls if call.get("method") == "post"
    )
    assert post_call["json"]["messages"][0]["content"] == "prefill"
    assert post_call["json"]["stop"] == ["###"]
    get_call = next(call for call in requests_stub.calls if call.get("method") == "get")
    assert get_call["kwargs"]["verify"] is True


def test_fallback_embed_moves_to_next_provider():
    class _EmbedProvider:
        def __init__(self, *, result=None, error=None):
            self.result = result
            self.error = error
            self.calls = 0

        def embed(self, **kwargs):
            self.calls += 1
            if self.error:
                raise self.error
            return self.result

    primary = _EmbedProvider(error=provider_system.ProviderError("no embed"))
    secondary = _EmbedProvider(result=[[0.1, 0.2]])

    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(),
    )

    result = fallback.embed(["text"])

    assert result == [[0.1, 0.2]]
    assert primary.calls == 1
    assert secondary.calls == 1


@pytest.mark.asyncio
async def test_fallback_aembed_recovers_from_failure():
    class _AsyncEmbedProvider:
        def __init__(self, *, result=None, error=None):
            self.result = result
            self.error = error
            self.calls = 0

        async def aembed(self, **kwargs):
            self.calls += 1
            if self.error:
                raise self.error
            return self.result

    primary = _AsyncEmbedProvider(error=provider_system.ProviderError("fail"))
    secondary = _AsyncEmbedProvider(result=[[1.0]])

    fallback = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=_fallback_config(),
    )

    result = await fallback.aembed(["payload"])

    assert result == [[1.0]]
    assert primary.calls == 1
    assert secondary.calls == 1


def test_get_provider_config_reads_env_file(monkeypatch, tmp_path):
    _enable_real_providers(monkeypatch)
    for name in [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "LM_STUDIO_ENDPOINT",
        "LM_STUDIO_MODEL",
        "DEVSYNTH_PROVIDER",
    ]:
        monkeypatch.delenv(name, raising=False)

    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath(".env").write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=envkey",
                "OPENAI_MODEL=env-model",
                "LM_STUDIO_ENDPOINT=http://127.0.0.1:9001",
                "LM_STUDIO_MODEL=alt-model",
                "DEVSYNTH_PROVIDER=stub",
            ]
        )
    )

    config = provider_system.get_provider_config()

    assert config["openai"]["api_key"] == "envkey"
    assert config["openai"]["model"] == "env-model"
    assert config["lmstudio"]["endpoint"] == "http://127.0.0.1:9001"
    assert config["lmstudio"]["model"] == "alt-model"
    assert config["default_provider"] == "stub"


def test_provider_factory_openai_success_path(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _Response:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def post(self, url, headers, json, timeout, **kwargs):
            self.calls.append(
                {
                    "url": url,
                    "headers": headers,
                    "json": json,
                    "timeout": timeout,
                    "kwargs": kwargs,
                }
            )
            return _Response({"choices": [{"message": {"content": "openai-sync"}}]})

    requests_stub = _RequestsStub()
    monkeypatch.setattr(provider_system, "requests", requests_stub)
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider("openai")

    result = provider.complete(
        "prompt",
        system_prompt="system",
        parameters={
            "messages": [{"role": "user", "content": "override"}],
            "temperature": 0.5,
            "max_tokens": 12,
            "stop": ["?"],
        },
    )

    assert result == "openai-sync"
    assert requests_stub.calls
    assert requests_stub.calls[0]["json"]["messages"][0]["content"] == "override"


def test_provider_factory_anthropic_requires_key(monkeypatch):
    _enable_real_providers(monkeypatch)
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider("anthropic")

    assert isinstance(provider, provider_system.NullProvider)
    assert "Anthropic API key is required" in provider.reason


def test_provider_factory_unknown_provider_uses_null(monkeypatch):
    _enable_real_providers(monkeypatch)
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "null")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider("unknown")

    assert isinstance(provider, provider_system.NullProvider)


def test_provider_factory_lmstudio_fallback_when_openai_missing(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def get(self, *args, **kwargs):  # noqa: ANN001 - stub
            raise self.exceptions.RequestException("lmstudio down")

    monkeypatch.setattr(provider_system, "requests", _RequestsStub())
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "stub")
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")

    provider = provider_system.ProviderFactory.create_provider()

    assert isinstance(provider, provider_system.StubProvider)


def test_openai_provider_async_paths(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _Response:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def post(self, url, headers, json, timeout, **kwargs):
            self.calls.append(
                {
                    "url": url,
                    "json": json,
                }
            )
            if url.endswith("/embeddings"):
                return _Response({"data": [{"embedding": [0.5, 0.25]}]})
            return _Response({"choices": [{"message": {"content": "openai-sync"}}]})

    class _AsyncResponse:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class _AsyncClient:
        def __init__(self, *_, **__):
            self.calls: list[dict[str, Any]] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):
            self.calls.append({"url": url, "json": json})
            if url.endswith("/embeddings"):
                return _AsyncResponse({"data": [{"embedding": [0.9, 0.1]}]})
            return _AsyncResponse(
                {"choices": [{"message": {"content": "openai-async"}}]}
            )

    class _HttpxStub:
        HTTPError = Exception

        def __init__(self):
            self.AsyncClient = _AsyncClient

    requests_stub = _RequestsStub()
    httpx_stub = _HttpxStub()
    monkeypatch.setattr(provider_system, "requests", requests_stub)
    monkeypatch.setattr(provider_system, "httpx", httpx_stub)

    provider = provider_system.OpenAIProvider(
        api_key="key",
        tls_config=provider_system.TLSConfig(verify=True, timeout=1.0),
        retry_config=_retry_config(),
    )

    assert provider.complete("prompt") == "openai-sync"
    assert provider.embed("vector") == [[0.5, 0.25]]
    assert asyncio.run(provider.acomplete("prompt")) == "openai-async"
    assert asyncio.run(provider.aembed(["vector"])) == [[0.9, 0.1]]


def test_provider_factory_real_module_branches(monkeypatch):
    module = _enable_real_providers(monkeypatch)
    _configure_settings(
        monkeypatch,
        provider_retry_metrics=True,
        provider_retry_conditions="status:429,TimeoutError",
        provider_max_retries=1,
        provider_initial_delay=0.0,
        provider_max_delay=0.0,
    )

    class _Response:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class RequestsHarness:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.fail_lmstudio_health = False
            self.fail_lmstudio_post = False
            self.fail_openai_post = False
            self.calls: list[tuple[str, str]] = []

        def get(self, url, *args, **kwargs):  # noqa: ANN001 - stub
            self.calls.append(("get", url))
            if self.fail_lmstudio_health:
                raise self.exceptions.RequestException("lmstudio health")
            return _Response({"data": [{"id": "model"}]})

        def post(
            self, url, headers=None, json=None, timeout=None, **kwargs
        ):  # noqa: ANN001 - stub
            self.calls.append(("post", url))
            if "openai" not in url and self.fail_lmstudio_post:
                raise self.exceptions.RequestException("lmstudio post")
            if "openai" in url and self.fail_openai_post:
                raise self.exceptions.RequestException("openai post")
            if url.endswith("/embeddings"):
                data = {"data": [{"embedding": [0.1, 0.9]}]}
            else:
                content = "openai chat" if "openai" in url else "lmstudio chat"
                data = {"choices": [{"message": {"content": content}}]}
            return _Response(data)

    class _AsyncResponse:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class _AsyncClient:
        def __init__(self, *_, **__):
            self.calls: list[str] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):  # noqa: ANN001 - stub
            self.calls.append(url)
            if url.endswith("/embeddings"):
                return _AsyncResponse({"data": [{"embedding": [0.6, 0.4]}]})
            return _AsyncResponse({"choices": [{"message": {"content": "async chat"}}]})

    def _simple_retry(**kwargs):  # noqa: ANN001 - stub decorator
        def decorator(func):
            def wrapper(*f_args, **f_kwargs):
                return func(*f_args, **f_kwargs)

            return wrapper

        return decorator

    requests_stub = RequestsHarness()
    monkeypatch.setattr(module, "requests", requests_stub)

    class _TLSMapping(dict):
        def __init__(self, verify: bool, timeout_val: float):
            super().__init__({"verify": verify})
            self._timeout = timeout_val

        def pop(self, key, default=None):  # noqa: ANN001 - mapping compatibility
            if key == "timeout":
                return self._timeout
            return super().pop(key, default)

    monkeypatch.setattr(
        module.TLSConfig,
        "as_requests_kwargs",
        lambda self: _TLSMapping(
            getattr(self, "verify", True), getattr(self, "timeout", 1.0) or 1.0
        ),
    )
    monkeypatch.setattr(module, "retry_with_exponential_backoff", _simple_retry)
    monkeypatch.setattr(
        module,
        "httpx",
        SimpleNamespace(AsyncClient=_AsyncClient, HTTPError=Exception),
    )

    # OpenAI success path covers parameter normalization and retry decorator
    monkeypatch.setenv("DEVSYNTH_OFFLINE", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    module.get_provider_config.cache_clear()
    openai_provider = module.ProviderFactory.create_provider("openai")
    assert isinstance(openai_provider, module.OpenAIProvider)
    assert (
        openai_provider.complete(
            "prompt",
            system_prompt="system",
            parameters={
                "messages": [{"role": "assistant", "content": "prefill"}],
                "temperature": 0.3,
                "max_tokens": 8,
            },
        )
        == "openai chat"
    )
    assert openai_provider.embed(["embed"]) == [[0.1, 0.9]]
    assert asyncio.run(openai_provider.acomplete("async")) == "async chat"
    assert asyncio.run(openai_provider.aembed(["async"])) == [[0.6, 0.4]]
    assert (
        openai_provider.complete_with_context(
            "ctx",
            [{"role": "system", "content": "sys"}],
        )
        == "openai chat"
    )

    # OpenAI fallback when LM Studio fails health check
    requests_stub.fail_lmstudio_health = True
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEVSYNTH_PROVIDER", "openai")
    monkeypatch.setenv("DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE", "true")
    module.get_provider_config.cache_clear()
    safe_provider = module.ProviderFactory.create_provider()
    assert isinstance(safe_provider, module.StubProvider)

    # LM Studio success and async helpers
    requests_stub.fail_lmstudio_health = False
    monkeypatch.delenv("DEVSYNTH_PROVIDER", raising=False)
    module.get_provider_config.cache_clear()
    lmstudio_provider = module.ProviderFactory.create_provider("lmstudio")
    assert isinstance(lmstudio_provider, module.LMStudioProvider)
    assert (
        lmstudio_provider.complete("prompt", parameters={"temperature": 0.2})
        == "lmstudio chat"
    )
    assert lmstudio_provider.embed(["vector"]) == [[0.1, 0.9]]
    assert asyncio.run(lmstudio_provider.acomplete("async")) == "async chat"
    assert asyncio.run(lmstudio_provider.aembed(["async"])) == [[0.6, 0.4]]
    assert lmstudio_provider.complete_with_context("ctx", []) == "lmstudio chat"

    # LM Studio explicit failure fallback
    requests_stub.fail_lmstudio_health = True
    module.get_provider_config.cache_clear()
    lmstudio_safe = module.ProviderFactory.create_provider("lmstudio")
    assert isinstance(lmstudio_safe, module.StubProvider)

    # Anthropic missing key and unsupported provider errors
    requests_stub.fail_lmstudio_health = False
    monkeypatch.setenv("DEVSYNTH_SAFE_DEFAULT_PROVIDER", "null")
    module.get_provider_config.cache_clear()
    anthropic_missing = module.ProviderFactory.create_provider("anthropic")
    assert isinstance(anthropic_missing, module.NullProvider)
    assert anthropic_missing.reason.startswith("Provider creation failed:")
    assert "Anthropic API key is required" in anthropic_missing.reason

    monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
    module.get_provider_config.cache_clear()
    anthropic_unsupported = module.ProviderFactory.create_provider("anthropic")
    assert isinstance(anthropic_unsupported, module.NullProvider)
    assert "Anthropic provider is not supported" in anthropic_unsupported.reason

    # Stub and unknown provider fallbacks
    module.get_provider_config.cache_clear()
    stub_provider = module.ProviderFactory.create_provider("stub")
    assert stub_provider.complete("hi").startswith("[stub:")

    module.get_provider_config.cache_clear()
    unknown_provider = module.ProviderFactory.create_provider("unknown")
    assert isinstance(unknown_provider, module.NullProvider)

    # ConfigurationError reload path
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    module.get_provider_config.cache_clear()
    cached_config = module.get_provider_config()

    def _unstable_get_settings(*args, **kwargs):
        if kwargs.get("reload"):
            return _make_settings()
        raise module.ConfigurationError("needs reload")

    monkeypatch.setattr(module, "get_settings", _unstable_get_settings)
    monkeypatch.setattr(module, "get_provider_config", lambda: cached_config)
    recovered_provider = module.ProviderFactory.create_provider("openai")
    assert isinstance(recovered_provider, module.OpenAIProvider)


def test_lmstudio_provider_async_paths(monkeypatch):
    _enable_real_providers(monkeypatch)

    class _Response:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class _RequestsStub:
        class exceptions:
            RequestException = Exception

        def __init__(self):
            self.calls: list[dict[str, Any]] = []

        def get(self, *args, **kwargs):  # noqa: ANN001 - stub
            return _Response({})

        def post(self, url, headers, json, timeout, **kwargs):
            self.calls.append({"url": url, "json": json})
            if url.endswith("/embeddings"):
                return _Response({"data": [{"embedding": [0.2, 0.8]}]})
            return _Response({"choices": [{"message": {"content": "lm-sync"}}]})

    class _AsyncResponse:
        def __init__(self, data: dict):
            self._data = data

        def raise_for_status(self):  # noqa: ANN001 - stub
            return None

        def json(self):  # noqa: ANN001 - stub
            return self._data

    class _AsyncClient:
        def __init__(self, *_, **__):
            self.calls: list[dict[str, Any]] = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, headers=None, json=None):
            self.calls.append({"url": url, "json": json})
            if url.endswith("/embeddings"):
                return _AsyncResponse({"data": [{"embedding": [0.7, 0.3]}]})
            return _AsyncResponse({"choices": [{"message": {"content": "lm-async"}}]})

    class _HttpxStub:
        HTTPError = Exception

        def __init__(self):
            self.AsyncClient = _AsyncClient

    requests_stub = _RequestsStub()
    httpx_stub = _HttpxStub()
    monkeypatch.setattr(provider_system, "requests", requests_stub)
    monkeypatch.setattr(provider_system, "httpx", httpx_stub)

    class _TLSKwargs(dict):
        def __init__(self, verify: bool, timeout_val: float):
            super().__init__({"verify": verify})
            self._timeout = timeout_val

        def pop(self, key, default=None):  # noqa: ANN001 - stub
            if key == "timeout":
                return self._timeout
            return super().pop(key, default)

    monkeypatch.setattr(
        provider_system.TLSConfig,
        "as_requests_kwargs",
        lambda self: _TLSKwargs(self.verify, self.timeout or 1.0),
    )

    provider = provider_system.LMStudioProvider(
        endpoint="http://localhost:1234",
        model="stub",
        tls_config=provider_system.TLSConfig(verify=True, timeout=1.0),
        retry_config=_retry_config(),
    )

    assert provider.complete("prompt") == "lm-sync"
    assert provider.embed("text") == [[0.2, 0.8]]
    assert asyncio.run(provider.acomplete("prompt")) == "lm-async"
    assert asyncio.run(provider.aembed(["text"])) == [[0.7, 0.3]]


def test_complete_helper_increments_metrics_and_propagates_error(monkeypatch):
    calls = _metrics_spy(monkeypatch)

    class _Provider:
        def __init__(self):
            self.called = 0

        def complete(self, **kwargs):
            self.called += 1
            raise provider_system.ProviderError("upstream failure")

    provider = _Provider()
    monkeypatch.setattr(provider_system, "get_provider", lambda **kwargs: provider)

    with pytest.raises(provider_system.ProviderError):
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

    with pytest.raises(provider_system.ProviderError) as excinfo:
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

    with pytest.raises(provider_system.ProviderError) as excinfo:
        await provider_system.aembed(["text"])

    assert "Embedding call failed" in str(excinfo.value)
    assert calls == ["aembed"]
    assert provider.called == 1
