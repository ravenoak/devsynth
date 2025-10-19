"""Additional coverage for :mod:`devsynth.adapters.provider_system`."""

from __future__ import annotations

import asyncio
import importlib
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def resume_coverage():
    """Ensure coverage collection restarts after global isolation teardown."""

    try:  # pragma: no cover - coverage always available during CI
        import coverage
    except Exception:  # pragma: no cover - safeguard for local runs
        yield
        return

    cov = coverage.Coverage.current()
    if cov is None:
        yield
        return

    try:  # pragma: no branch - idempotent start
        cov.start()
    except Exception:  # pragma: no cover - ignore double starts
        pass
    yield


@pytest.fixture()
def provider_module(monkeypatch: pytest.MonkeyPatch):
    """Reload provider system with deterministic settings and clean cache."""

    import sys
    from types import ModuleType

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
        import devsynth.adapters.provider_system as provider_system

        # Clear any existing caches after module import
        if hasattr(provider_system.get_provider_config, "cache_clear"):
            provider_system.get_provider_config.cache_clear()

        # Mock get_provider_config directly in the module to return the desired config
        def mock_get_provider_config():
            return {
                "default_provider": "openai",
                "openai": {
                    "api_key": None,
                    "model": "gpt-4",
                    "base_url": "https://api.openai.com/v1",
                },
                "lmstudio": {"endpoint": "http://127.0.0.1:1234", "model": "default"},
                "openrouter": {
                    "api_key": None,
                    "model": None,
                    "base_url": "https://openrouter.ai/api/v1",
                },
                "retry": {
                    "max_retries": 1,
                    "initial_delay": 0.1,
                    "exponential_base": 2.0,
                    "max_delay": 1.0,
                    "jitter": False,
                    "track_metrics": True,
                    "conditions": [],
                },
                "fallback": {"enabled": True, "order": ["stub"]},
                "circuit_breaker": {
                    "enabled": False,
                    "failure_threshold": 1,
                    "recovery_timeout": 1.0,
                },
            }

        monkeypatch.setattr(
            provider_system, "get_provider_config", mock_get_provider_config
        )

        yield provider_system

        # Clean up caches
        if hasattr(provider_system.get_provider_config, "cache_clear"):
            provider_system.get_provider_config.cache_clear()
    finally:
        # Don't restore the original settings module here - keep the mock active for the test
        pass

    # Restore original settings module after test completes
    if original_settings is not None:
        sys.modules["devsynth.config.settings"] = original_settings


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

    monkeypatch.setattr(
        "devsynth.adapters.provider_system.retry_with_exponential_backoff", fake_retry
    )

    base = module.BaseProvider()
    decorator = base.get_retry_decorator()
    assert callable(decorator)
    assert captured["max_retries"] == 1
    assert captured["initial_delay"] == 0.1
    assert captured["exponential_base"] == 2.0
    assert captured["track_metrics"] is True
    assert captured["on_retry"] == base._emit_retry_telemetry


def test_retry_decorator_respects_track_metrics_flag(monkeypatch, provider_module):
    """Providers disable retry telemetry when track_metrics is ``False``."""

    module = provider_module
    captured = {}

    def fake_retry(**kwargs):  # noqa: ANN001
        captured.update(kwargs)

        def decorator(func):  # noqa: ANN001
            return func

        return decorator

    monkeypatch.setattr(module, "retry_with_exponential_backoff", fake_retry)

    base = module.BaseProvider(
        retry_config={
            "max_retries": 2,
            "initial_delay": 0.2,
            "exponential_base": 3.0,
            "max_delay": 1.0,
            "jitter": False,
            "track_metrics": False,
            "conditions": [],
        }
    )

    base.get_retry_decorator()

    assert captured["max_retries"] == 2
    assert captured["track_metrics"] is False


def test_stub_provider_deterministic_embeddings(provider_module):
    """Stub provider deterministic hashing returns floats in [0, 1).

    ReqID: coverage-provider-system
    """

    module = provider_module
    stub = module.StubProvider()
    values = stub.embed("hello world")
    assert len(values) == 1
    assert all(0 <= number < 1 for number in values[0])


def test_create_tls_config_uses_settings(provider_module):
    """TLS helper mirrors verification flags and certificate paths from settings."""

    module = provider_module
    settings = SimpleNamespace(
        tls_verify=False,
        tls_cert_file="cert.pem",
        tls_key_file="key.pem",
        tls_ca_file="ca.pem",
    )

    tls = module._create_tls_config(settings)

    assert tls.verify is False
    assert tls.cert_file == "cert.pem"
    assert tls.key_file == "key.pem"
    assert tls.ca_file == "ca.pem"


def test_provider_factory_prefers_explicit_tls_config(provider_module):
    """Passing a TLS config overrides derived settings for stub providers."""

    module = provider_module
    custom_tls = module.TLSConfig(verify=False, cert_file="custom.pem")

    provider = module.ProviderFactory.create_provider(
        "stub", tls_config=custom_tls, retry_config={"max_retries": 0}
    )

    assert provider.tls_config is custom_tls
    assert provider.retry_config["max_retries"] == 0


def test_fallback_async_skips_open_circuit(provider_module):
    """Fallback iterates to the next provider when the first circuit is open."""

    module = provider_module

    class PrimaryProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def aembed(self, **kwargs):  # noqa: ANN001
            self.calls += 1
            return [[0.0]]

    class SecondaryProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def aembed(self, **kwargs):  # noqa: ANN001
            self.calls += 1
            return [[1.0]]

    primary = PrimaryProvider()
    secondary = SecondaryProvider()
    config = {
        "retry": module.get_provider_config()["retry"],
        "fallback": {"enabled": True, "order": ["primary", "secondary"]},
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 1,
            "recovery_timeout": 1.0,
        },
    }

    class CircuitStub(SimpleNamespace):
        def __init__(self, state: str) -> None:  # noqa: D401 - simple recorder
            super().__init__(state=state, failures=0, successes=0)

        def _record_failure(self) -> None:
            self.failures += 1
            self.state = "open"

        def _record_success(self) -> None:
            self.successes += 1
            self.state = "closed"

    fallback = module.FallbackProvider(
        providers=[primary, secondary],
        config=config,
    )
    fallback.circuit_breakers = {
        "primary": CircuitStub("open"),
        "secondary": CircuitStub("closed"),
    }

    async def _runner() -> None:
        result = await fallback.aembed(["payload"])

        assert result == [[1.0]]
        assert primary.calls == 0
        assert secondary.calls == 1

    asyncio.run(_runner())
