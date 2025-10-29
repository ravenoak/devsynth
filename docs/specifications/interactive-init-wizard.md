---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-19
status: review
tags:

- specification

title: Interactive Init Wizard
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

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?

- BDD scenarios in [`tests/behavior/features/interactive_init_wizard.feature`](../../tests/behavior/features/interactive_init_wizard.feature) and [`tests/behavior/features/general/setup_wizard.feature`](../../tests/behavior/features/general/setup_wizard.feature) cover both auto-confirmed and cancelled runs of the setup wizard.
- Step bindings in [`tests/behavior/steps/test_interactive_init_wizard_steps.py`](../../tests/behavior/steps/test_interactive_init_wizard_steps.py) validate environment-driven initialization.
- Unit coverage in [`tests/unit/application/cli/test_setup_wizard.py`](../../tests/unit/application/cli/test_setup_wizard.py) ensures the Typer CLI plumbing writes configuration and handles abort paths.

## Intended Behaviors

- **Environment-controlled defaults** – When `DEVSYNTH_INIT_*` variables are present, the wizard auto-fills project root, language, features, and offline flags, enabling unattended initialization. Verified by [`tests/behavior/features/interactive_init_wizard.feature`](../../tests/behavior/features/interactive_init_wizard.feature).
- **Persisted project configuration** – A successful run writes `.devsynth/project.yaml` with the selected options and enables requested features. Covered by [`tests/behavior/steps/test_interactive_init_wizard_steps.py`](../../tests/behavior/steps/test_interactive_init_wizard_steps.py) and [`tests/unit/application/cli/test_setup_wizard.py`](../../tests/unit/application/cli/test_setup_wizard.py).
- **Graceful cancellation** – Declining confirmation leaves no configuration artifacts and emits a cancellation message, as demonstrated in [`tests/behavior/features/general/setup_wizard.feature`](../../tests/behavior/features/general/setup_wizard.feature).


## Specification

## Acceptance Criteria

- When environment defaults are present, running the wizard writes `.devsynth/project.yaml` with the configured backend, language, feature flags, and offline mode.
- Cancelling the wizard leaves no configuration files behind and emits a "Cancelled" message.
- Wizard output surfaces success or cancellation through the bridge so calling automation can assert the outcome.
