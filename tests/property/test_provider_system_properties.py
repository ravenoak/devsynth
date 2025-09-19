"""Property-based tests for provider fallback behavior.

Issue: issues/edrr-integration-with-real-llm-providers.md ReqID: PRV-001
"""

from itertools import product

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


@pytest.mark.property
@pytest.mark.medium
@given(
    st.lists(
        st.floats(
            min_value=0.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
            width=32,
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=25)
def test_fallback_expected_call_cost_matches_probability(success_probabilities):
    """Expected provider calls equal the cumulative failure prefixes.

    Issue: issues/edrr-integration-with-real-llm-providers.md ReqID: PRV-001
    """

    normalized = [float(max(0.0, min(1.0, p))) for p in success_probabilities]

    def _run_once(sequence):
        providers = [DummyProvider(success=value) for value in sequence]
        fb = FallbackProvider(
            providers=providers, config={"retry": {}, "fallback": {"enabled": True}}
        )
        try:
            fb.complete("prompt")
        except ProviderError:
            pass
        return sum(provider.calls for provider in providers)

    expectation_from_enumeration = 0.0
    for outcomes in product([False, True], repeat=len(normalized)):
        call_count = _run_once(outcomes)
        weight = 1.0
        for probability, outcome in zip(normalized, outcomes):
            weight *= probability if outcome else (1.0 - probability)
        expectation_from_enumeration += call_count * weight

    expectation_from_prefixes = 0.0
    surviving_prefix_probability = 1.0
    for probability in normalized:
        expectation_from_prefixes += surviving_prefix_probability
        surviving_prefix_probability *= 1.0 - probability

    assert expectation_from_enumeration == pytest.approx(
        expectation_from_prefixes, rel=1e-6, abs=1e-6
    )
