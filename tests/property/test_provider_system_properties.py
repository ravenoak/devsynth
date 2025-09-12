"""Property-based tests for provider fallback behavior.

Issue: issues/edrr-integration-with-real-llm-providers.md ReqID: PRV-001
"""

import pytest

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover
    pytest.skip("hypothesis not available", allow_module_level=True)

from devsynth.adapters.provider_system import (
    BaseProvider,
    FallbackProvider,
    ProviderError,
)


class DummyProvider(BaseProvider):
    def __init__(self, success: bool) -> None:
        super().__init__()
        self.success = success
        self.calls = 0

    def complete(self, prompt: str, **_kw: object) -> str:
        self.calls += 1
        if self.success:
            return "ok"
        raise ProviderError("fail")


@pytest.mark.property
@pytest.mark.medium
@given(st.lists(st.booleans(), min_size=1, max_size=5))
@settings(max_examples=50)
def test_fallback_provider_stops_at_first_success(outcomes):
    """FallbackProvider stops after the first successful provider.

    Issue: issues/edrr-integration-with-real-llm-providers.md ReqID: PRV-001
    """

    providers = [DummyProvider(s) for s in outcomes]
    fb = FallbackProvider(
        providers=providers, config={"retry": {}, "fallback": {"enabled": True}}
    )
    if any(outcomes):
        assert fb.complete("prompt") == "ok"
        idx = outcomes.index(True)
        for i, p in enumerate(providers):
            if i <= idx:
                assert p.calls == 1
            else:
                assert p.calls == 0
    else:
        with pytest.raises(ProviderError):
            fb.complete("prompt")
        for p in providers:
            assert p.calls == 1
