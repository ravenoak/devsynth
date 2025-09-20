---
author: DevSynth Team
date: '2025-09-20'
status: review
tags:
- implementation
- invariants
title: Provider System Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Provider System Invariants
</div>

# Provider System Invariants

The provider system manages multiple LLM backends and fallback logic.

## Default Provider Configuration

`get_provider_config` always returns a configuration where
`config['default_provider']` is present and corresponds to a provider
configuration block.

## Fallback Termination

`FallbackProvider.complete` attempts providers sequentially and stops at the
first successful provider. The algorithm either returns the successful result or
raises `ProviderError` if all providers fail.

```python
from devsynth.adapters.provider_system import BaseProvider, FallbackProvider, ProviderError

class Dummy(BaseProvider):
    def __init__(self, ok):
        super().__init__()
        self.ok = ok
        self.calls = 0
    def complete(self, *_args, **_kw):
        self.calls += 1
        if self.ok:
            return "ok"
        raise ProviderError("boom")

providers = [Dummy(False), Dummy(True), Dummy(True)]
fb = FallbackProvider(providers=providers, config={"retry": {}, "fallback": {"enabled": True}})
assert fb.complete("prompt") == "ok"
assert providers[0].calls == 1 and providers[1].calls == 1 and providers[2].calls == 0
```

This behavior is exercised by
`tests/property/test_provider_system_properties.py::test_fallback_provider_stops_at_first_success`.【F:tests/property/test_provider_system_properties.py†L1-L53】

## Measured Retry Cost and Expected Provider Calls

The sequential fallback contract yields a closed-form expectation for how many
providers are invoked before either a success or an aggregate failure:

\[
\mathbb{E}[\text{calls}] = \sum_{i=1}^{n} \prod_{j=1}^{i-1} (1 - p_j),
\]

where `p_j` is the probability that provider `j` succeeds when it is asked to
complete the request. The property-based regression
`tests/property/test_provider_system_properties.py::test_fallback_expected_call_cost_matches_probability`
enumerates every success/failure outcome for up to five providers, weights each
outcome by its probability mass, and confirms that the measured average number
of provider invocations matches the cumulative failure-prefix formula above.
This supplements
`test_fallback_provider_stops_at_first_success`, which proves that only the
prefix up to the first success is ever charged.【F:tests/property/test_provider_system_properties.py†L32-L98】

Two representative scenarios, derived from the automated enumeration, illustrate
the retry budget:

| Provider success probabilities | Expected provider calls |
| --- | --- |
| (0.7, 0.5, 0.2) | 1 + 0.3 + 0.3 × 0.5 = **1.45** |
| (0.3, 0.4, 0.8) | 1 + 0.7 + 0.7 × 0.6 = **2.12** |

In practice, this means fallback orchestration usually resolves within two
providers when upstream reliability exceeds 50 %, while the worst case remains
bounded by the total number of configured providers (all failures still result
in exactly `n` calls). The measured expectation guides quota planning for paid
providers and justifies leaving retry counters at the default of one attempt per
provider when failure probabilities remain below 30 %.【F:tests/property/test_provider_system_properties.py†L56-L98】

## References

- Issue: [issues/edrr-integration-with-real-llm-providers.md](../issues/edrr-integration-with-real-llm-providers.md)
- Tests: [tests/property/test_provider_system_properties.py](../tests/property/test_provider_system_properties.py) (Hypothesis coverage) and [tests/unit/providers/test_provider_system_additional.py](../../tests/unit/providers/test_provider_system_additional.py) (offline defaults and retry plumbing).【F:tests/property/test_provider_system_properties.py†L1-L98】【F:tests/unit/providers/test_provider_system_additional.py†L1-L118】

## Coverage Signal (2025-09-20)

- Fast regression tests [`tests/unit/providers/test_provider_system_additional.py`](../../tests/unit/providers/test_provider_system_additional.py) simulate offline safeguards, safe-provider selection, and retry configuration plumbing without requiring optional HTTP extras. A focused `pytest --cov=devsynth.adapters.provider_system` run records 16.86 % line coverage, improving on the prior 12 % baseline and proving the fallback invariants remain enforced when toggling environment flags.【F:tests/unit/providers/test_provider_system_additional.py†L1-L118】【F:issues/tmp_cov_provider_system.json†L1-L1】
