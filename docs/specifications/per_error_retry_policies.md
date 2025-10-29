---
author: DevSynth Team
date: '2025-07-30'
last_reviewed: '2025-07-30'
status: draft
tags:
- specification
- retry
- error-handling
title: Per-Error Retry Policies
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Per-Error Retry Policies
</div>

# Per-Error Retry Policies

## Problem

Global retry settings cannot accommodate exceptions that require custom retry
limits or disabling retries altogether.

## Proof

Implement a mapping of exception types to per-error policies consumed by
``retry_with_exponential_backoff``. Policies may specify ``max_retries`` and a
``retry`` flag that overrides the global behaviour. Policies match against
subclasses of the configured exception types so that a ``ValueError`` entry also
governs ``FileNotFoundError``.

When metrics are enabled, use ``prometheus_client`` counters to record when
named policies permit or suppress retries for observability.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/per_error_retry_policies.feature`](../../tests/behavior/features/per_error_retry_policies.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
