---
title: "Requirements Wizard"
author: "DevSynth Team"
date: "2025-09-05"
last_reviewed: "2025-09-19"
status: "review"
version: "0.1.0a1"
tags:
  - "specification"
  - "requirements"
  - "logging"
---

# Summary

The requirements wizard collects core requirement attributes, records a structured audit trail, and persists selections to both JSON output and `.devsynth/project.yaml` so downstream tooling shares a single source of truth.

## Socratic Checklist
- **What is the problem?** Contributors need an auditable, interactive flow that captures requirement metadata while supporting backtracking.
- **What proofs confirm the solution?** Behavior and unit suites exercise CLI/WebUI interactions, logging guarantees, and persistence flows.

## Motivation

Accurate requirement capture underpins EDRR, prioritization, and onboarding flows. The wizard must therefore provide deterministic prompts, structured logging, and config synchronization.

## What proofs confirm the solution?

- CLI coverage comes from [`tests/behavior/features/requirements_wizard.feature`](../../tests/behavior/features/requirements_wizard.feature) and [`tests/behavior/features/general/requirements_wizard.feature`](../../tests/behavior/features/general/requirements_wizard.feature).
- Logging and priority persistence are exercised by [`tests/behavior/requirements_wizard/features/general/requirements_wizard_logging.feature`](../../tests/behavior/requirements_wizard/features/general/requirements_wizard_logging.feature) and the focused suite in [`tests/behavior/requirements_wizard/features/general/logging_and_priority.feature`](../../tests/behavior/requirements_wizard/features/general/logging_and_priority.feature).
- Unit tests [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py) and [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py) verify persistence, logging, and error paths.
- WebUI parity is captured by navigation tests in [`tests/behavior/features/general/requirements_wizard_navigation.feature`](../../tests/behavior/features/general/requirements_wizard_navigation.feature) and the invariant notes in [`docs/implementation/webui_rendering_invariants.md`](../implementation/webui_rendering_invariants.md).

## Intended Behaviors

- **Step-by-step prompts** – The wizard solicits title, description, type, priority, and constraints using `UXBridge`, allowing users to step backward without losing earlier answers.
- **Structured logging** – Each prompt emits a `wizard_step` log entry that captures the current step and selected value; save attempts log `requirements_saved` or `requirements_save_failed` with `exc_info`.
- **Synchronized persistence** – Completing the wizard writes `requirements_wizard.json` and updates `.devsynth/project.yaml` with the latest priority and constraints, keeping CLI and WebUI consumers aligned.

## Specification

- The wizard records each step with `DevSynthLogger`, including the step name and chosen value.
- `DevSynthLogger` accepts exception objects via `exc_info` and renders full stack traces without crashing.
- The final priority selection is written to `.devsynth/project.yaml` via the configuration loader.
- The CLI flow relies on `UXBridge` abstractions so the WebUI can reuse the same logic through shared bridges.

## Acceptance Criteria

- Running the wizard produces log entries for each step and a final `requirements_saved` event when persistence succeeds.
- The saved JSON output and `.devsynth/project.yaml` contain the latest priority and constraint values even after navigating backward.
- Supplying `exc_info` to `DevSynthLogger` during persistence failures does not raise errors, and the exception is re-raised for callers.
