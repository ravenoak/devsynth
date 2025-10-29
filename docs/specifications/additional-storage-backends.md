---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:

- specification

title: Additional Storage Backends
version: 0.1.0a1
---

<!--
Required metadata fields:
- author: document author
- date: creation date
- last_reviewed: last review date
- status: draft | review | published
- tags: search keywords
- title: short descriptive name
- version: specification version
-->

# Summary

DevSynth currently persists structured memory through a single TinyDB backend.
To support deployments that require external or cloud storage, the memory
system must expose an adapter interface and provide at least one additional
backend implementation.

## Socratic Checklist
- What is the problem?
  - Memory persistence is tightly coupled to TinyDB and cannot be switched to
    other services.
- What proofs confirm the solution?
  - A pluggable adapter interface and S3-backed implementation verified by
    integration tests.

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/additional_storage_backends.feature`](../../tests/behavior/features/additional_storage_backends.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.


Allow projects to opt into cloud or database storage without changing the
`MemoryManager` API.  Configuration should determine the backend at runtime so
tests and examples remain hermetic.

## Specification

- Introduce a `StorageAdapter` protocol extending the existing `MemoryStore`
  contract and exposing a `backend_type` attribute used for selection.
- Implement an `S3MemoryAdapter` using boto3 that stores each `MemoryItem` as a
  JSON object in an S3 bucket.
- Extend `MemoryManager` so that when no adapters are supplied it inspects the
  `memory_store_type` setting and instantiates the matching adapter.  When the
  value is `s3`, the manager configures the adapter with the bucket name from
  `s3_bucket_name`.

## Required Environment Variables

- `DEVSYNTH_MEMORY_STORE` – selects the backend (`s3` enables the S3 adapter).
- `DEVSYNTH_S3_BUCKET` – name of the bucket for persisted items.
- Standard AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
  optionally `AWS_DEFAULT_REGION`) so boto3 can authenticate.

## Acceptance Criteria

- Given `DEVSYNTH_MEMORY_STORE=s3` and an available bucket, `MemoryManager`
  persists and retrieves items using `S3MemoryAdapter`.
- Documentation describes required environment variables and usage examples.
