---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-10-21
status: review
tags:
  - specification

title: Interactive Requirements Flow CLI
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

Prompt-toolkit integration and Textual parity introduce richer controls without disrupting the existing collector orchestration. This update clarifies how the CLI flow negotiates capabilities advertised by `UXBridge` so the same workflow can drive Typer prompts, prompt-toolkit dialogs, or Textual forms.

## What proofs confirm the solution?

- BDD scenarios in [`tests/behavior/features/interactive_requirements_flow_cli.feature`](../../tests/behavior/features/interactive_requirements_flow_cli.feature), [`tests/behavior/features/cli_ux_enhancements.feature`](../../tests/behavior/features/cli_ux_enhancements.feature), and [`tests/behavior/features/requirements_wizard_navigation.feature`](../../tests/behavior/features/requirements_wizard_navigation.feature) verify prompt-toolkit multi-selects, navigation shortcuts, and structured summaries.
- Unit coverage in [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py) exercises the success path and cancellation handling for `RequirementsCollector`, including capability negotiation with the bridge adapter.
- End-to-end orchestration is mirrored by [`tests/behavior/steps/test_interactive_flow_steps.py`](../../tests/behavior/steps/test_interactive_flow_steps.py), which binds the collector to the UX bridge abstraction and now asserts consistent navigation events across bridges.

## Intended Behaviors

- **Prompt-driven collection** – The CLI collector asks for name, language, and features via `UXBridge` and refuses to persist if the user declines confirmation. Covered by [`tests/behavior/features/interactive_requirements_flow_cli.feature`](../../tests/behavior/features/interactive_requirements_flow_cli.feature).
- **Structured persistence** – On confirmation the collector normalizes comma- or semicolon-separated feature inputs and writes `interactive_requirements.json`. Verified by [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py).
- **User feedback** – The collector surfaces "Requirements saved" or "Cancelled" messages through the bridge, ensuring scripts can assert outcomes. Exercised in [`tests/unit/application/requirements/test_interactions.py`](../../tests/unit/application/requirements/test_interactions.py).
- **Capability-aware prompts** – When the bridge advertises `supports_multi_select`, the collector uses prompt-toolkit style checkboxes to gather feature toggles and maintains keyboard shortcuts for navigation. Behaviour described in [`tests/behavior/features/cli_ux_enhancements.feature`](../../tests/behavior/features/cli_ux_enhancements.feature).


## Specification

## Acceptance Criteria

- Confirming the flow writes `interactive_requirements.json` with normalized feature lists and displays "Requirements saved".
- Declining confirmation leaves no output file and surfaces "Cancelled".
- The collector returns control without raising when the bridge answers `back` before confirmation, enabling scripted retries.
- Navigation through prompt-toolkit or Textual shortcuts (e.g., `Ctrl+B`, `Ctrl+R`) produces the same persisted artefacts as the linear baseline.

## References

- [Issue: Interactive Requirements Flow CLI](../../issues/interactive-requirements-flow-cli.md)
- [BDD: interactive_requirements_flow_cli.feature](../../tests/behavior/features/interactive_requirements_flow_cli.feature)
