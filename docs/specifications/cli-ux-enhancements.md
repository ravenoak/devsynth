---
author: DevSynth Team
date: 2025-10-21
last_reviewed: 2025-10-21
status: review
tags:
  - specification
  - cli
  - ux
  - textual
  - prompt-toolkit
  - rich
  - uxbridge
  - requirements
  - dialectical
  - socratic
  - systems-thinking
title: CLI UX Enhancements
version: 0.1.0-alpha.2
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

The CLI currently delivers workflows through Typer and Rich but forces users to navigate long, linear prompt sequences that lack history, completions, or persistent context views. This specification defines a multi-channel improvement plan that layers prompt-toolkit interactions, a Textual-powered TUI, and richer Rich layouts on top of the existing `UXBridge` abstraction so that requirements and setup wizards become faster, more accessible, and easier to audit.

## Socratic Checklist
- **What is the problem?** Users must remember sentinel commands like `back`, cannot review earlier answers while responding to new prompts, and receive wizard summaries as long transcripts rather than structured overviews.
- **What proofs confirm the solution?** Behavioural features codified in `tests/behavior/features/cli_ux_enhancements.feature`, `tests/behavior/features/requirements_wizard_navigation.feature`, and `tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature` exercise the prompt-toolkit, Textual, and Rich flows respectively. Additional unit test placeholders will be registered under `tests/unit/application/cli/` to validate bridge fallbacks.

## Motivation

A dialectical review highlighted a tension between linear prompts (clarity, low implementation cost) and interactive shells (discoverability, resilience). By harmonising these perspectives through systems thinking, we can keep `UXBridge` as the single orchestration surface while letting different presentation layers—baseline Rich prompts, prompt-toolkit sessions, and Textual scenes—negotiate the best experience for each environment. This holistic approach supports neurodiverse operators, reduces input friction, and aligns with the roadmap goal of cross-interface parity.

## Specification

### 1. Prompt-Toolkit Augmentation (FR-90, FR-91)
- Provide a `PromptToolkitSession` adapter that wraps `prompt_toolkit.PromptSession` with history, tab completion, validation, and checkbox dialogs.
- Update `CLIUXBridge` methods to prefer the adapter when the `DEVSYNTH_NONINTERACTIVE` safeguard is unset and prompt-toolkit is available; gracefully fall back to existing Rich prompts otherwise.
- Extend wizard flows to replace yes/no confirmation loops with multi-select prompts and to surface inline help text for each choice.

### 2. Textual TUI Shell (FR-91, FR-92)
- Implement a `TextualUXBridge` that renders wizard steps in dedicated panes (form input, live summary, contextual help, progress) and synchronises responses with the shared workflow logic.
- Launch the Textual app through a new `devsynth tui` command (alias `devsynth init --tui`) that binds the same orchestrators used by the CLI and WebUI.
- Ensure keyboard navigation (arrow keys, hotkeys for back/next/overview) replaces sentinel commands such as `back`, while respecting accessibility themes defined for the CLI.

### 3. Rich Layout Enhancements (FR-93)
- Replace sequential `display_result` calls in wizard summaries with Rich tables, panels, and tree layouts that highlight configuration choices, feature toggles, and next steps.
- Update command help generation to support collapsible sections and filtered views, enabling users to focus on relevant tasks without scanning full transcripts.
- Maintain sanitisation and logging hooks so that structured output can be captured by existing diagnostic tooling.

### 4. Cross-Bridge Consistency (FR-90 – FR-93)
- Document shared interaction contracts between `CLIUXBridge`, `PromptToolkitSession`, `TextualUXBridge`, and the NiceGUI bridge to guarantee that workflows behave identically regardless of shell.
- Expand the `UXBridge` contract to include optional capabilities (e.g., `supports_multi_select`, `supports_layout_panels`) with negotiated fallbacks.
- Capture decision records explaining how non-interactive automation, logging, and accessibility settings propagate across the presentation layers.

## Acceptance Criteria

1. When prompt-toolkit is installed, CLI prompts expose history navigation, autocompletion, and checkbox-style multi-selects; uninstalling the dependency reverts to Rich prompts without breaking flows.
2. Requirements and setup wizards allow users to move backward or jump to summaries using keyboard navigation or on-screen controls instead of typing literal sentinel commands.
3. Running `poetry run devsynth tui` launches a Textual interface that displays inputs, summaries, and help in separate panes while persisting answers through the existing workflow orchestration.
4. Wizard summaries and command help output structured Rich layouts that pass accessibility contrast checks and remain sanitised for log capture.
5. Automated tests cover prompt-toolkit fallbacks, Textual bridge handshakes, and Rich layout rendering, with traceability recorded in the requirements matrix.

## References

- [System Requirement FR-90 – FR-93](../system_requirements_specification.md#311-multi-channel-user-experience)
- [BDD: cli_ux_enhancements.feature](../../tests/behavior/features/cli_ux_enhancements.feature)
- [BDD: requirements_wizard_navigation.feature](../../tests/behavior/features/requirements_wizard_navigation.feature)
- [BDD: shared_uxbridge_across_cli_and_webui.feature](../../tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature)
- [Architecture: UXBridge](../architecture/uxbridge.md)
- [Architecture: CLI/WebUI Mapping](../architecture/cli_webui_mapping.md)
