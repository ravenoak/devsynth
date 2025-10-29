---
author: DevSynth Team
date: '2025-07-24'
last_reviewed: '2025-07-24'
status: draft
tags:
- specification
- retry
- reliability
- metrics
title: Retry Predicates Specification
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Retry Predicates Specification
</div>

## Problem

Transient HTTP failures are currently detected only through exceptions. Responses with error status codes are returned to callers without automatic retry, reducing resilience.

## Proof

- A unit test mocks an HTTP response returning status code 503 followed by 200 and verifies the retry predicate triggers a retry and increments Prometheus metrics.
- A behavior-driven test demonstrates that functions using retry predicates eventually succeed after transient server errors.
- A unit test passes an exception type as a retry condition and confirms trigger and suppress metrics are recorded.

## Configuration Options

- `retry_predicates`: list or dictionary of predicates evaluated on successful
  results. Predicates may be callables or integer HTTP status codes. When a
  dictionary is provided, keys name the predicate and the name is used in
  metrics.
- `track_metrics`: enables Prometheus metrics. Predicate evaluations increment
  `devsynth_retry_conditions_total` using labels
  `predicate:<name>:trigger` or `predicate:<name>:suppress` to record whether a
  predicate allowed the result or triggered a retry.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/retry_predicates.feature`](../../tests/behavior/features/retry_predicates.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
