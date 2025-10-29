---
author: DevSynth Team
date: '2025-02-19'
last_reviewed: '2025-02-19'
status: draft
tags:
  - reliability
  - retries
  - circuit-breaker

title: Reliability Patterns
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Reliability Patterns
</div>

# Reliability Patterns

DevSynth provides helpers for implementing resilient services. This guide
covers two core utilities from `devsynth.fallback`.

## Configurable Retry Conditions

`retry_with_exponential_backoff` accepts a `condition_callbacks` mapping that
allows custom logic to veto retries. Each callback receives the raised
exception and the current attempt number:

```python
from devsynth.fallback import retry_with_exponential_backoff
from devsynth.metrics import get_retry_condition_metrics

policy = {"stop": lambda exc, attempt: attempt < 1}

@retry_with_exponential_backoff(condition_callbacks=policy, max_retries=3)
def unstable():
    raise RuntimeError("boom")

try:
    unstable()
except RuntimeError:
    pass

print(get_retry_condition_metrics())
```

Metrics record whether each callback triggered or suppressed further retries.

## Circuit Breaker Hooks

`CircuitBreaker` emits hooks on state transitions. Hooks receive the protected
function's name so callers can update dashboards or trigger alerts.

```python
from devsynth.fallback import CircuitBreaker

events = []
cb = CircuitBreaker(on_open=lambda name: events.append(f"open:{name}"))

@cb
def flaky():
    raise ValueError("oops")

try:
    flaky()
except ValueError:
    pass
```

`events` now contains `['open:flaky']` and circuit breaker metrics are updated via
`devsynth.metrics`.
