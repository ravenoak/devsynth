from __future__ import annotations

import pytest

from devsynth.adapters.provider_system import (
    BaseProvider,
    FallbackProvider,
    ProviderError,
)
from devsynth.exceptions import DevSynthError
from devsynth.metrics import (
    get_circuit_breaker_state_metrics,
    get_provider_metrics,
    inc_circuit_breaker_state,
    reset_metrics,
)

pytestmark = pytest.mark.fast


def _retry_config() -> dict[str, object]:
    return {
        "max_retries": 3,
        "initial_delay": 0.1,
        "exponential_base": 2.0,
        "max_delay": 1.0,
        "jitter": True,
        "track_metrics": True,
        "conditions": [],
    }


def _fallback_config() -> dict[str, object]:
    return {
        "retry": _retry_config(),
        "fallback": {"enabled": True, "order": ["breakerprobe"]},
        "circuit_breaker": {
            "enabled": True,
            "failure_threshold": 1,
            "recovery_timeout": 1.0,
        },
    }


class _BreakerProbeProvider(BaseProvider):
    def __init__(self, *, retry_config: dict[str, object]) -> None:
        super().__init__(retry_config=retry_config)
        self.should_fail_sync = False
        self.should_fail_async = False
        self.sync_exception: Exception = RuntimeError("sync failure")
        self.async_exception: Exception = RuntimeError("async failure")

    def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, object] | None = None,
    ) -> str:
        if self.should_fail_sync:
            raise self.sync_exception
        return f"sync:{prompt}"

    async def acomplete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        *,
        parameters: dict[str, object] | None = None,
    ) -> str:
        if self.should_fail_async:
            raise self.async_exception
        return f"async:{prompt}"


class _RecordingBreaker:
    def __init__(self, method_name: str, failure_threshold: int = 1) -> None:
        self.method_name = method_name
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.state = "closed"

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            inc_circuit_breaker_state(func.__name__, "OPEN")
            raise DevSynthError(
                f"Circuit breaker for {func.__name__} is open",
                error_code="CIRCUIT_OPEN",
            )

        try:
            result = func(*args, **kwargs)
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                inc_circuit_breaker_state(func.__name__, "OPEN")
            raise
        else:
            if self.state != "closed":
                inc_circuit_breaker_state(func.__name__, "CLOSED")
            self.state = "closed"
            self.failure_count = 0
            return result

    def _record_failure(self) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
        inc_circuit_breaker_state(self.method_name, "OPEN")

    def _record_success(self) -> None:
        if self.state != "closed":
            inc_circuit_breaker_state(self.method_name, "CLOSED")
        self.state = "closed"
        self.failure_count = 0


@pytest.mark.asyncio
async def test_base_provider_retry_harness_records_jitter(async_retry_harness) -> None:
    """Async harness exercises jitter and telemetry without real sleeps."""

    harness = async_retry_harness
    outcome = await harness.invoke(fail_times=2)

    assert outcome.result == "ok-3"
    assert [event.attempt for event in harness.telemetry] == [1, 2]
    assert harness.jitter[:2] == [0.25, 0.75]
    assert harness.sleeps == pytest.approx([0.15, 0.375])

    telemetry_delays = [round(event.delay, 3) for event in harness.telemetry]
    assert telemetry_delays == [0.15, 0.375]

    provider_metrics = get_provider_metrics()
    assert provider_metrics.get("retry") == 2


@pytest.mark.asyncio
async def test_fallback_provider_async_breaker_failure_emits_metrics() -> None:
    """Async failures open the breaker and surface ``ProviderError``."""

    reset_metrics()
    config = _fallback_config()
    provider = _BreakerProbeProvider(retry_config=config["retry"])
    fallback = FallbackProvider(providers=[provider], config=config)
    breaker = _RecordingBreaker("acomplete")
    fallback.circuit_breakers[fallback._provider_type(provider)] = breaker

    provider.should_fail_async = True
    with pytest.raises(ProviderError) as excinfo:
        await fallback._call_async(provider, "acomplete", prompt="demo")

    assert "provider _breakerprobeprovider failed" in str(excinfo.value).lower()
    assert breaker.state == "open"
    metrics = get_circuit_breaker_state_metrics()
    assert metrics.get("acomplete:OPEN") == 1

    provider.should_fail_async = False
    with pytest.raises(ProviderError) as excinfo_open:
        await fallback._call_async(provider, "acomplete", prompt="demo-two")

    assert "circuit breaker is open" in str(excinfo_open.value)
    metrics_after = get_circuit_breaker_state_metrics()
    assert metrics_after.get("acomplete:OPEN") == 1


def test_fallback_provider_sync_breaker_failure_emits_metrics() -> None:
    """Sync failures propagate to ``ProviderError`` and increment metrics."""

    reset_metrics()
    config = _fallback_config()
    provider = _BreakerProbeProvider(retry_config=config["retry"])
    fallback = FallbackProvider(providers=[provider], config=config)
    breaker = _RecordingBreaker("complete")
    fallback.circuit_breakers[fallback._provider_type(provider)] = breaker

    provider.should_fail_sync = True
    with pytest.raises(ProviderError) as excinfo:
        fallback.complete("demo")

    assert "All providers failed" in str(excinfo.value)
    assert breaker.state == "open"
    metrics = get_circuit_breaker_state_metrics()
    assert metrics.get("complete:OPEN") == 1

    provider.should_fail_sync = False
    with pytest.raises(ProviderError) as excinfo_open:
        fallback.complete("demo-two")

    assert "circuit breaker" in str(excinfo_open.value).lower()
    metrics_after = get_circuit_breaker_state_metrics()
    assert metrics_after.get("complete:OPEN") == 2
