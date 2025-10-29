---
title: Requirements Wizard
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-19
status: review
version: 0.1.0a1
tags:
  - specification
  - requirements
  - logging
---

# Summary

This hyphenated slug preserves historical references to the requirements
wizard while aligning with the canonical
[Requirements Wizard](requirements_wizard.md) specification. It documents
the interactive flow that gathers requirement metadata across the CLI and
WebUI so downstream automation shares a single source of truth.

## Socratic Checklist

- **What is the problem?** Contributors need an auditable flow that captures
  requirement details, allows backtracking, and persists results for both
  interfaces.
- **What proofs confirm the solution?** Behavior features and focused unit
  tests exercise prompting, logging, and persistence guarantees end to end.

## Motivation

Accurate requirement capture underpins prioritization, onboarding, and
recursive coordination flows. Maintaining this alias ensures any
references to the historic hyphenated path continue to surface the vetted
requirements workflow and its supporting evidence.

## Intended Behaviors

- **Step-by-step prompts** – The wizard solicits title, description,
  requirement type, priority, and constraints through `UXBridge`, allowing
  users to revisit earlier answers without losing progress.
- **Structured logging** – Each interaction emits `wizard_step` entries and
  records save attempts via `requirements_saved` or
  `requirements_save_failed` with `exc_info` for diagnostics.
- **Synchronized persistence** – Completing the flow writes
  `requirements_wizard.json` and updates `.devsynth/project.yaml` so CLI
  and WebUI consumers observe the same state.

## Traceability

- **Behavior coverage** –
  [`tests/behavior/features/requirements_wizard.feature`](../../tests/behavior/features/requirements_wizard.feature),
  [`tests/behavior/features/general/requirements_wizard.feature`](../../tests/behavior/features/general/requirements_wizard.feature),
  and [`tests/behavior/features/requirements_wizard_navigation.feature`](../../tests/behavior/features/requirements_wizard_navigation.feature)
  validate saving, cancellation, and navigation across CLI and WebUI
  surfaces.
- **Unit coverage** –
  [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py)
  exercises `RequirementsCollector` persistence paths, while
  [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py)
  confirms logging hooks and error handling.
- **Invariant notes** –
  [`docs/implementation/webui_invariants.md`](../implementation/webui_invariants.md)
  captures wizard state convergence guarantees relied upon by the WebUI
  bridge.

## Acceptance Criteria

- Wizard prompts allow backtracking and produce a saved
  `requirements_wizard.json` file when the session completes.
- Cancellation leaves no persisted file artefacts on disk.
- Logging records each prompt as a `wizard_step` entry and mirrors the final
  priority in both the JSON output and `.devsynth/project.yaml`.
- The behavior and unit suites referenced above continue to pass, providing
  regression coverage for the documented guarantees.
