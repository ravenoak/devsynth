from __future__ import annotations

import pytest

from devsynth.adapters import provider_system
from tests.helpers.dummies import DummyProvider


@pytest.mark.fast
def test_fallback_provider_complete_uses_next_provider() -> None:
    config = {
        "fallback": {"enabled": True},
        "retry": {
            "max_retries": 0,
            "initial_delay": 0.0,
            "exponential_base": 1.0,
            "max_delay": 0.0,
            "jitter": False,
            "track_metrics": False,
            "conditions": [],
        },
        "circuit_breaker": {"enabled": False},
    }

    primary = DummyProvider(
        "primary",
        failures={"complete": provider_system.ProviderError("primary failure")},
    )
    secondary = DummyProvider("secondary")

    fallback_provider = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=config,
        provider_factory=None,
    )

    result = fallback_provider.complete("Generate requirements")

    assert result == "secondary-complete"
    assert [call for call, _ in primary.calls] == ["complete"]
    assert [call for call, _ in secondary.calls] == ["complete"]


@pytest.mark.fast
def test_fallback_provider_complete_raises_after_exhaustion() -> None:
    config = {
        "fallback": {"enabled": True},
        "retry": {
            "max_retries": 0,
            "initial_delay": 0.0,
            "exponential_base": 1.0,
            "max_delay": 0.0,
            "jitter": False,
            "track_metrics": False,
            "conditions": [],
        },
        "circuit_breaker": {"enabled": False},
    }

    primary = DummyProvider(
        "primary",
        failures={"complete": provider_system.ProviderError("primary failed")},
    )
    secondary = DummyProvider(
        "secondary",
        failures={"complete": provider_system.ProviderError("secondary failed")},
    )

    fallback_provider = provider_system.FallbackProvider(
        providers=[primary, secondary],
        config=config,
        provider_factory=None,
    )

    with pytest.raises(provider_system.ProviderError) as exc_info:
        fallback_provider.complete("Draft spec")

    assert "secondary failed" in str(exc_info.value)
    assert [call for call, _ in primary.calls] == ["complete"]
    assert [call for call, _ in secondary.calls] == ["complete"]


@pytest.mark.fast
def test_embed_wraps_unexpected_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    failing_provider = DummyProvider(
        "stub",
        failures={"embed": ValueError("boom")},
    )

    monkeypatch.setattr(
        provider_system,
        "get_provider",
        lambda provider_type=None, fallback=True: failing_provider,
    )

    with pytest.raises(provider_system.ProviderError) as exc_info:
        provider_system.embed("text", fallback=False)

    assert "boom" in str(exc_info.value)
    assert [call for call, _ in failing_provider.calls] == ["embed"]
