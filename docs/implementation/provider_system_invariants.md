---
author: DevSynth Team
date: '2025-09-12'
status: draft
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
`tests/property/test_provider_system_properties.py::test_fallback_provider_stops_at_first_success`.

## References

- Issue: [issues/edrr-integration-with-real-llm-providers.md](../issues/edrr-integration-with-real-llm-providers.md)
- Test: [tests/property/test_provider_system_properties.py](../tests/property/test_provider_system_properties.py)
