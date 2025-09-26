---
author: AI Assistant
date: '2025-09-26'
status: published
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
`ProjectSetupPages` within the DevSynth WebUI, pairing each invariant with
targeted fast tests and focused coverage evidence.

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
surfacing a clear confirmation message.【F:src/devsynth/interface/webui/rendering.py†L224-L269】

[`test_handle_requirements_navigation_cancel_clears_state`](../../tests/unit/interface/test_webui_rendering_module.py)
verifies the reset logic and the emitted status message.

## Saving Requirements Normalizes Payloads

`_save_requirements` writes the collected requirement details to
`requirements_wizard.json`, splits comma-delimited constraints into a list, and
clears the wizard's temporary state to avoid accidental resubmission.【F:src/devsynth/interface/webui/rendering.py†L188-L222】

[`test_save_requirements_clears_temporary_keys`](../../tests/unit/interface/test_webui_rendering_module.py)
confirms the persisted structure and cleanup side effects.

## Progress Completion Cascades Remain Sanitized

Fast WebUI suites verify that completing the top-level progress indicator drives every subtask to completion even when `streamlit.success` is unavailable. The fallback writes sanitized labels to `st.write`, and nested subtasks emit the same escaped completion message, keeping UI telemetry consistent with CLI progress semantics.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L1022-L1056】【F:tests/unit/interface/test_webui_rendering_progress.py†L95-L314】

## Streamlit Fallbacks Stay Sanitized

When Streamlit omits the `info` or `markdown` helpers, the WebUI implementation drops back to `st.write` without losing sanitization: info/highlight messages flow through `write` with HTML entities escaped, errors still render via `st.error`, and legacy markup converts to Markdown before the fallback executes.【F:tests/unit/interface/test_webui_behavior_checklist_fast.py†L574-L647】 These fast paths guarantee the rendering layer remains safe when optional components are absent.

## Coverage Evidence

A focused fast sweep combines the rendering module regression harness, progress
summaries, and wizard navigation suites so coverage data reflects the rendering
surface without pulling the entire Streamlit stack into scope.

| Module | Coverage | Evidence |
| --- | --- | --- |
| `devsynth.interface.webui.rendering` | 29 % | `poetry run pytest -o addopts="" tests/unit/interface/test_webui_rendering_module.py tests/unit/interface/test_webui_rendering_progress.py tests/unit/interface/test_webui_progress_cascade_fast.py tests/unit/interface/test_webui_bridge_wizard_navigation_fast.py --cov=devsynth.interface.webui.rendering --cov=devsynth.interface.webui_bridge --cov-report=term --cov-report=json:test_reports/webui_rendering_bridge_coverage.json --cov-report=html:test_reports/htmlcov_webui_rendering_bridge --cov-fail-under=0`【779285†L1-L33】【8fff97†L3-L10】 |
| `devsynth.interface.webui_bridge` | 25 % | `poetry run pytest -o addopts="" tests/unit/interface/test_webui_rendering_module.py tests/unit/interface/test_webui_rendering_progress.py tests/unit/interface/test_webui_progress_cascade_fast.py tests/unit/interface/test_webui_bridge_wizard_navigation_fast.py --cov=devsynth.interface.webui.rendering --cov=devsynth.interface.webui_bridge --cov-report=term --cov-report=json:test_reports/webui_rendering_bridge_coverage.json --cov-report=html:test_reports/htmlcov_webui_rendering_bridge --cov-fail-under=0`【779285†L1-L33】【79e500†L1-L9】 |

The run persists refreshed artifacts at
`test_reports/webui_rendering_bridge_coverage.json` and
`test_reports/htmlcov_webui_rendering_bridge/index.html` for future audits and
plan traceability.【b90c51†L1-L3】

## References

- Tests: `tests/unit/interface/test_webui_rendering_module.py`, `tests/unit/interface/test_webui_rendering_progress.py`
- Specification: [docs/specifications/webui-requirements-wizard-with-wizardstate.md](../specifications/webui-requirements-wizard-with-wizardstate.md)
