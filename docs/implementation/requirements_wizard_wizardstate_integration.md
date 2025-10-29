---
author: DevSynth Team
date: '2025-07-31'
last_reviewed: "2025-09-21"
status: review
tags:
- implementation
- webui
- wizard
- state-management
title: Requirements Wizard WizardState Integration Guide
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Requirements Wizard WizardState Integration Guide
</div>

# Requirements Wizard WizardState Integration Guide

The WebUI requirements wizard now delegates all multi-step state management to
`WizardState`, ensuring that navigation, persistence, and completion semantics
match the guarantees exercised by the gather wizard. This note captures the
integration details and the executable evidence that keeps the behaviour stable.

## Summary

- `WebUIBridge` exposes helpers that build a `WizardStateManager` from the
  active Streamlit session, providing a single entry point for wizard state
  orchestration across front-ends.【F:src/devsynth/interface/webui_bridge.py†L333-L371】
- The requirements and gather wizards use those helpers to load
  `WizardState`, capture widget input, clamp navigation, and reset state after
  completion or cancellation.【F:src/devsynth/interface/webui/rendering.py†L274-L358】【F:src/devsynth/interface/webui/rendering.py†L404-L470】
- Behaviour and unit tests demonstrate that values persist when navigating, the
  wizard resets after saving, and missing session state triggers clear
  diagnostics.【F:tests/behavior/features/webui_requirements_wizard_with_wizardstate.feature†L1-L24】【F:tests/behavior/steps/test_webui_requirements_wizard_with_wizardstate_steps.py†L1-L165】【F:tests/unit/interface/test_webui_bridge_targeted.py†L127-L165】

## Implementation Details

### Bridge-level coordination

`WebUIBridge.create_wizard_manager` guards access to Streamlit's session state
and constructs a `WizardStateManager` with the requested defaults. The instance
method `get_wizard_manager` reuses the current session automatically, while
`get_wizard_state` returns the underlying `WizardState` for consumers that only
need the state object.【F:src/devsynth/interface/webui_bridge.py†L333-L371】 These helpers replace ad-hoc
instantiation and ensure missing `session_state` surfaces as a `DevSynthError`
instead of failing silently.【F:tests/unit/interface/test_webui_bridge_targeted.py†L149-L165】

### Requirements wizard flow

`ProjectSetupPages._requirements_wizard` now requests a manager from
`WebUIBridge` and uses the resulting `WizardState` to drive every form step. The
implementation:

1. Seeds defaults (title, description, type, priority, constraints) and binds
   the wizard to Streamlit via `WebUIBridge.create_wizard_manager`.【F:src/devsynth/interface/webui/rendering.py†L274-L310】
2. Persists user input back into `WizardState` on each step, handling invalid
   selections defensively while preserving existing answers.【F:src/devsynth/interface/webui/rendering.py†L312-L354】
3. Routes navigation through the manager so `WizardState` advances, retreats, or
   cancels consistently, including validation for incomplete steps.【F:src/devsynth/interface/webui/rendering.py†L224-L258】
4. On save, serialises the collected data, marks the wizard complete, resets the
   underlying state, and clears temporary widget keys before returning to the
   first step.【F:src/devsynth/interface/webui/rendering.py†L186-L215】

### Gather wizard alignment

The resource gather wizard shares the same helper, ensuring both wizards follow
identical creation, reset, and validation paths. This keeps state invariants
consistent as additional wizards adopt the pattern.【F:src/devsynth/interface/webui/rendering.py†L404-L470】

## Evidence

- **Behaviour coverage.** The BDD scenarios confirm that titles and descriptions
  persist when navigating backward and that completing the wizard resets the
  state while saving a requirements summary. The step definitions use a mocked
  Streamlit session to exercise the real `_requirements_wizard` implementation
  and assert the resulting `WizardState` values.【F:tests/behavior/features/webui_requirements_wizard_with_wizardstate.feature†L1-L24】【F:tests/behavior/steps/test_webui_requirements_wizard_with_wizardstate_steps.py†L37-L165】
- **Unit coverage.** Targeted tests ensure the bridge helper returns the same
  session-backed `WizardState` across calls and that missing session state raises
  `DevSynthError`, preventing silent failures in production or tests.【F:tests/unit/interface/test_webui_bridge_targeted.py†L127-L165】

Together these artefacts demonstrate the completed integration and provide
regressions for the wizard state management guarantees.
