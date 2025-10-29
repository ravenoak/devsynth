---
author: AI Assistant
date: 2025-08-23
last_reviewed: 2025-08-23
status: review
tags:
  - specification
  - logging

title: Logging Setup Utilities
version: 0.1.0a1
---

# Summary

Specifies low-level logging utilities that provide JSON formatting and request-context support.

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/logging_setup.feature`](../../tests/behavior/features/logging_setup.feature) ensure termination and expected outcomes.【F:tests/behavior/features/logging_setup.feature†L1-L10】
- Unit suites [`tests/unit/logging/test_logging_setup_contexts.py`](../../tests/unit/logging/test_logging_setup_contexts.py) and [`tests/unit/logging/test_logging_setup_additional_paths.py`](../../tests/unit/logging/test_logging_setup_additional_paths.py) exercise CLI wiring, sandbox redirection, and secret redaction behaviors referenced by the invariants.【F:tests/unit/logging/test_logging_setup_contexts.py†L1-L173】【F:tests/unit/logging/test_logging_setup_additional_paths.py†L1-L185】
- Implementation guidance in [`docs/implementation/logging_invariants.md`](../implementation/logging_invariants.md) now sits at review status with a targeted coverage sweep (41.15 % line coverage for `logging_setup.py`) captured in [`issues/tmp_cov_logging_setup.json`](../../issues/tmp_cov_logging_setup.json).【F:docs/implementation/logging_invariants.md†L1-L66】【F:issues/tmp_cov_logging_setup.json†L1-L1】
- Finite state transitions and bounded loops guarantee termination.

Components require structured logs with optional request identifiers without configuring logging at import time.

## Specification
- Offer a `JSONFormatter` for structured logs.
- Provide `set_request_context` and `clear_request_context` helpers.
- Delay log directory creation until explicitly configured.

## Acceptance Criteria
- JSON logs include request identifiers when context is set.
- Importing the module does not create log directories.
