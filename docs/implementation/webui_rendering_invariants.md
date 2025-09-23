---
author: AI Assistant
date: '2025-09-16'
status: active
tags:
  - implementation
  - invariants
title: WebUI Rendering Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; WebUI Rendering Invariants
</div>

# WebUI Rendering Invariants

This note records behavioural guarantees for the Streamlit pages assembled by
`ProjectSetupPages` within the DevSynth WebUI.

## Requirements Wizard Validates Incrementally

`ProjectSetupPages._validate_requirements_step` ensures each wizard step has the
inputs it needs before navigation is allowed, preventing half-complete
requirements from being persisted.【F:src/devsynth/interface/webui/rendering.py†L172-L183】

[`test_validate_requirements_step_requires_fields`](../../tests/unit/interface/test_webui_rendering_module.py)
walks through each step and demonstrates that empty values are rejected until
the requisite field is populated.

## Cancel Actions Reset State

`_handle_requirements_navigation` clears temporary form inputs and resets the
wizard when a user cancels, keeping subsequent sessions free of stale values and
surfacing a clear confirmation message.【F:src/devsynth/interface/webui/rendering.py†L221-L266】

[`test_handle_requirements_navigation_cancel_clears_state`](../../tests/unit/interface/test_webui_rendering_module.py)
verifies the reset logic and the emitted status message.

## Saving Requirements Normalizes Payloads

`_save_requirements` writes the collected requirement details to
`requirements_wizard.json`, splits comma-delimited constraints into a list, and
clears the wizard's temporary state to avoid accidental resubmission.【F:src/devsynth/interface/webui/rendering.py†L185-L218】

[`test_save_requirements_clears_temporary_keys`](../../tests/unit/interface/test_webui_rendering_module.py)
confirms the persisted structure and cleanup side effects.

## Progress Completion Cascades Remain Sanitized

Fast WebUI suites verify that completing the top-level progress indicator drives every subtask to completion even when `streamlit.success` is unavailable. The fallback writes sanitized labels to `st.write`, and nested subtasks emit the same escaped completion message, keeping UI telemetry consistent with CLI progress semantics.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L1022-L1056】

## Streamlit Fallbacks Stay Sanitized

When Streamlit omits the `info` or `markdown` helpers, the WebUI implementation drops back to `st.write` without losing sanitization: info/highlight messages flow through `write` with HTML entities escaped, errors still render via `st.error`, and legacy markup converts to Markdown before the fallback executes.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L574-L647】 These fast paths guarantee the rendering layer remains safe when optional components are absent.

## References

- Tests: `tests/unit/interface/test_webui_rendering_module.py`
- Specification: [docs/specifications/webui-requirements-wizard-with-wizardstate.md](../specifications/webui-requirements-wizard-with-wizardstate.md)
