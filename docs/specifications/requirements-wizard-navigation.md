---
author: DevSynth Team
date: 2025-10-21
last_reviewed: 2025-10-21
status: review
tags:
  - specification
  - requirements
  - wizard
  - navigation
  - textual
  - prompt-toolkit
  - accessibility
  - uxbridge
title: Requirements Wizard Navigation
version: 0.1.0-alpha.2
---

# Summary

The requirements wizard must evolve from a linear, sentinel-command-driven sequence into an adaptive flow that supports keyboard navigation, contextual summaries, and cross-bridge parity. This specification defines navigation behaviours shared across the CLI, Textual TUI, and WebUI implementations.

## Socratic Checklist
- **What is the problem?** Users have to type literal commands such as `back` to revisit prior steps and cannot see a consolidated summary while making choices, leading to errors and fatigue.
- **What proofs confirm the solution?** Behaviour-driven scenarios in `requirements_wizard_navigation.feature` and `cli_ux_enhancements.feature` outline navigation, summary viewing, and parity expectations.

## Motivation

Through dialectical evaluation we balance structure (predictable steps) with flexibility (non-linear navigation). Systems thinking emphasises that navigation events must propagate consistently across all bridges to keep documentation, automation, and accessibility in sync.

## Specification

### 1. Navigation Model
- Represent wizard steps as a finite state machine with explicit transitions for `next`, `previous`, `review`, and `cancel`.
- Allow jump navigation to any prior step when the bridge advertises `supports_history`.
- Persist responses when users move backward or review summaries, ensuring that edits propagate downstream.

### 2. Contextual Summary Pane
- Maintain a live summary of collected inputs (project metadata, requirement attributes, feature toggles) visible alongside prompts in Textual and WebUI, and accessible through a quick-view command in the CLI.
- Use Rich panels/tables for CLI summaries and equivalent components in Textual/WebUI, keeping sanitisation intact.

### 3. Input Enhancements
- Provide prompt-toolkit multi-select dialogs for feature toggles and list questions, including inline descriptions for each option.
- Support keyboard shortcuts (`Ctrl+B` for back, `Ctrl+R` for review) with fallbacks to explicit commands when a bridge lacks shortcut capabilities.

### 4. Validation and Persistence
- Validate inputs on navigation (e.g., required fields cannot be skipped) and surface consistent error messaging across bridges.
- Ensure that saved outputs (JSON, YAML) remain unchanged regardless of the navigation path taken.

## Acceptance Criteria

1. Users can navigate backward or forward without typing sentinel strings, using either keyboard shortcuts or onscreen controls.
2. A live summary updates after each step and remains available during navigation across CLI, Textual, and WebUI implementations.
3. Multi-select prompts with inline help replace repetitive yes/no confirmations for feature toggles, with graceful fallback when prompt-toolkit is absent.
4. Navigation paths (including review loops) persist responses and produce identical output artifacts compared to the linear baseline.

## References

- [System Requirement FR-90 – FR-93](../system_requirements_specification.md#311-multi-channel-user-experience)
- [Specification: CLI UX Enhancements](cli-ux-enhancements.md)
- [Specification: Shared UXBridge across CLI, Textual TUI, and WebUI](shared-uxbridge-across-cli-and-webui.md)
- [BDD: requirements_wizard_navigation.feature](../../tests/behavior/features/requirements_wizard_navigation.feature)
