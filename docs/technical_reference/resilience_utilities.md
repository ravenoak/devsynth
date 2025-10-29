---

author: DevSynth Team
date: '2025-07-20'
last_reviewed: '2025-07-20'
status: draft
tags:
  - technical-reference
  - resiliency
  - utilities

title: Resilience Utilities
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; Resilience Utilities
</div>

# Resilience Utilities

This document outlines best practices for using the retry, circuit breaker and
bulkhead helpers provided in `devsynth.fallback`.

## Overview

`retry_with_exponential_backoff`, `with_fallback`, `CircuitBreaker`, and
`Bulkhead` are utilities that help services degrade gracefully when something
goes wrong. They should be used together to prevent cascading failures and limit
resource exhaustion.

## Best Practices

1. **Bounded Retries**
   - Always configure `max_retries` on `retry_with_exponential_backoff` to avoid
     infinite loops.
   - Use jitter to prevent thundering herd effects when many retries happen
     concurrently.

2. **Circuit Breaker Configuration**
   - Choose a reasonable `failure_threshold` based on the error rate you can
     tolerate.
   - Set a short `recovery_timeout` for non-critical services so that healthy
     instances can recover quickly.
   - Log transitions between states, but avoid logging every single call.

3. **Bulkhead Usage**
   - Set `max_concurrent_calls` according to available resources (for example,
     CPU cores or worker processes).
   - Keep `max_queue_size` small to fail fast instead of allowing unbounded
     waiting.
   - The Bulkhead implementation uses semaphores for concurrency control;
     avoid long-running tasks when possible to keep queues flowing.

4. **Combining Patterns**
   - Apply a circuit breaker inside a bulkhead to both limit concurrency and
     stop calling external services that are consistently failing.
   - Use the retry decorator on idempotent operations only.

5. **Logging Considerations**
   - Excessive logging in tight loops can reduce performance. The provided
     utilities log state transitions and errors but avoid verbose output during
     normal operation.

## Example

```python
from devsynth.fallback import retry_with_exponential_backoff, CircuitBreaker, Bulkhead

bulkhead = Bulkhead(max_concurrent_calls=4, max_queue_size=2)
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

@breaker
@bulkhead
@retry_with_exponential_backoff(max_retries=2)
def fetch_data():
    ...  # call an external service
```

These helpers work together to retry temporary failures, open the circuit when
failures persist and limit how many calls run at once.
