---
author: OpenAI Assistant
date: 2025-01-15
last_reviewed: 2025-01-15
status: draft
tags:
  - specification
  - lmstudio
  - testing
title: LM Studio Integration
version: 0.1.0a1
---

# Summary

Provides a deterministic mock LM Studio server for testing without external dependencies.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/lmstudio_integration.feature`](../../tests/behavior/features/lmstudio_integration.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.


Tests relying on LM Studio should operate without network access. A local mock server emulates the LM Studio API to keep tests fast and reliable.

## Specification

The `lmstudio_mock` fixture starts an in-memory FastAPI server exposing `/v1/models`, `/v1/chat/completions`, and `/v1/embeddings`. It streams tokens for chat completions, returns dummy embeddings, and can simulate HTTP errors. The fixture yields an object exposing `base_url` and error controls.

## Acceptance Criteria

- `lmstudio_mock` returns a server object with a usable `base_url`.
- Tests use the fixture instead of live LM Studio services.
- Error triggering is available for negative test scenarios.
