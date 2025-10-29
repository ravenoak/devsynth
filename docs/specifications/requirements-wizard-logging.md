---
title: Requirements Wizard Logging
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-19
status: review
version: 0.1.0a1
tags:
  - specification
  - logging
  - requirements
---

# Summary

This document keeps the historic hyphenated slug for requirements wizard
logging aligned with the canonical
[Requirements Wizard Logging](requirements_wizard_logging.md) specification.
It details the structured diagnostics emitted by the interactive flow so
compliance, auditing, and debugging remain verifiable across interfaces.

## Socratic Checklist

- **What is the problem?** We must capture wizard interactions with
  structured, high-fidelity logs to support audits and post-run analysis.
- **What proofs confirm the solution?** Behavior features and unit tests
  assert that each step produces the expected log entries and that errors
  surface `exc_info` details when persistence fails.

## Motivation

The requirements wizard drives onboarding and prioritization decisions.
Clear logging demonstrates what choices were made, confirms configuration
updates, and accelerates troubleshooting when persistence encounters
errors.

## Intended Behaviors

- **Step tracing** – Each prompt emits a JSON `wizard_step` record capturing
  the current step and selected value.
- **Success auditing** – Completing the flow writes a `requirements_saved`
  entry with the persisted priority and mirrors the selection in the saved
  configuration.
- **Failure visibility** – Write failures produce a `requirements_save_failed`
  entry that includes `exc_info` so downstream tooling can diagnose issues.

## Traceability

- **Behavior coverage** –
  [`tests/behavior/requirements_wizard/features/general/requirements_wizard_logging.feature`](../../tests/behavior/requirements_wizard/features/general/requirements_wizard_logging.feature)
  and [`tests/behavior/requirements_wizard/features/general/logging_and_priority.feature`](../../tests/behavior/requirements_wizard/features/general/logging_and_priority.feature)
  confirm step logging, JSON payloads, and configuration synchronization.
- **Unit coverage** –
  [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py)
  exercises success and error logging, while
  [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py)
  validates that persisted data mirrors the logged selections.
- **Invariant notes** – [`docs/implementation/logging_invariants.md`](../implementation/logging_invariants.md)
  records system-wide logging guarantees that back these flows.

## Acceptance Criteria

- Running the wizard emits `wizard_step` entries for every prompt and records
  a final `requirements_saved` event with the chosen priority.
- Persistence failures capture `exc_info` in `requirements_save_failed` and
  leave the saved configuration untouched.
- JSON logs and configuration updates remain synchronized across CLI and
  WebUI executions.
- Referenced behavior and unit suites continue passing to enforce the
  documented guarantees.
