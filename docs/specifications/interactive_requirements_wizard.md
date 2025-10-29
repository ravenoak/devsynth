---

title: "Interactive Requirements Wizard"
date: "2025-06-16"
last_reviewed: "2025-09-19"
version: "0.1.0a1"
tags:
  - "specification"
  - "requirements"
  - "ux"

status: "review"
author: "DevSynth Team"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Interactive Requirements Wizard
</div>

# Interactive Requirements Wizard

This specification describes the guided workflow for collecting
requirements and constraints. The wizard runs in both the CLI and the
NiceGUI WebUI through the `UXBridge` interface.

## Workflow Overview

1. Title
2. Description
3. Requirement type
4. Priority
5. Constraints
6. Confirmation and save


The wizard allows moving backward by typing `back` in the CLI or using
the *Back* button in the WebUI. Collected data is saved to a JSON file
named `requirements_wizard.json`.

## Design Choices

- **Step Driven** – Each question is presented as a discrete step so the user

  can review and revise answers.

- **Bridge Integration** – All prompts use `UXBridge.ask_question` and

  `UXBridge.confirm_choice` to remain interface agnostic.

## Constraints

- Inputs must be validated according to requirement type and priority options.
- The wizard state is stored in memory until the user confirms completion.

## What proofs confirm the solution?

- BDD scenarios in [`tests/behavior/features/interactive_requirements_wizard.feature`](../../tests/behavior/features/interactive_requirements_wizard.feature) and [`tests/behavior/features/general/requirements_wizard_navigation.feature`](../../tests/behavior/features/general/requirements_wizard_navigation.feature) exercise the CLI bridge and WebUI navigation paths end to end.
- Unit coverage in [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py) and [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py) verifies persistence, logging, and error handling.
- WebUI invariants remain synchronized with the wizard contract per [`docs/implementation/webui_rendering_invariants.md`](../implementation/webui_rendering_invariants.md).

## Intended Behaviors

- **Bridge-driven question flow** – `UXBridge.ask_question` and `confirm_choice` collect title, description, type, priority, and constraints with explicit "back" handling so earlier answers persist. See [`tests/behavior/features/interactive_requirements_wizard.feature`](../../tests/behavior/features/interactive_requirements_wizard.feature) and [`tests/behavior/steps/test_interactive_requirements_steps.py`](../../tests/behavior/steps/test_interactive_requirements_steps.py).
- **Synchronized persistence** – Completion writes `requirements_wizard.json`, updates `.devsynth/project.yaml`, and emits `wizard_step` audit logs for each prompt. Verified by [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py) and [`tests/unit/application/requirements/test_wizard.py`](../../tests/unit/application/requirements/test_wizard.py).
- **WebUI parity** – Streamlit-backed flows reuse the shared wizard state helpers to move forward/backward without losing data. Exercised by [`tests/behavior/features/general/requirements_wizard_navigation.feature`](../../tests/behavior/features/general/requirements_wizard_navigation.feature) with bindings in [`tests/behavior/steps/test_requirements_wizard_navigation_steps.py`](../../tests/behavior/steps/test_requirements_wizard_navigation_steps.py).

## Acceptance Criteria

- Navigating backward returns to the previous step without discarding earlier answers, and the final priority survives in both `requirements_wizard.json` and `.devsynth/project.yaml`.
- Completing the wizard produces a success message, persists structured JSON output, and emits a `wizard_step` log entry per prompt.
- Persisting configuration failures surface a `requirements_save_failed` log with `exc_info` populated before bubbling the exception.

## Implementation Status

This feature is **implemented** with persistent storage and navigation controls across CLI and WebUI surfaces.
