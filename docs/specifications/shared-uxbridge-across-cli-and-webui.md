---
author: DevSynth Team
date: 2025-10-21
last_reviewed: 2025-10-21
status: review
tags:
  - specification
  - uxbridge
  - cli
  - textual
  - webui
  - architecture
  - accessibility
  - systems-thinking
  - dialectical
title: Shared UXBridge across CLI, Textual TUI, and WebUI
version: 0.1.0-alpha.2
---

# Summary

DevSynth uses `UXBridge` to abstract user interactions across multiple front ends. To support the planned Textual TUI and prompt-toolkit enriched CLI, this specification formalises the shared contract so that CLI, Textual, and NiceGUI WebUI implementations remain interchangeable while preserving accessibility and automation safeguards.

## Socratic Checklist
- **What is the problem?** Divergent front-end implementations risk inconsistent behaviours, forcing users to relearn workflows and complicating automated testing across interfaces.
- **What proofs confirm the solution?** Behaviour-driven features—`shared_uxbridge_across_cli_and_webui.feature`, `cli_ux_enhancements.feature`, and `requirements_wizard_navigation.feature`—assert parity across bridges. Architecture diagrams in `docs/architecture/cli_textual_uxbridge.md` illustrate message flow consistency.

## Motivation

From a dialectical perspective, we must balance rapid CLI iteration against the structural integrity required for GUI parity. Systems thinking reveals that a robust bridge contract reduces coupling, enabling each presentation layer (Typer CLI, Textual TUI, NiceGUI WebUI) to evolve without breaking core workflows. This alignment mitigates regression risk, keeps accessibility guarantees uniform, and simplifies future integrations like voice-controlled or remote dashboards.

## Specification

### 1. Capability Negotiation
- Extend the `UXBridge` protocol with optional capability flags (`supports_history`, `supports_multi_select`, `supports_layout_panels`).
- Provide discovery helpers so workflows can adapt prompts when a capability is absent (e.g., fall back to yes/no when multi-select is unavailable).

### 2. Interaction Contract
- Standardise method signatures for `ask_question`, `ask_multi_select`, `confirm_choice`, `display_layout`, and `stream_progress`.
- Document error handling, sanitisation, and localisation requirements shared across bridges.
- Enforce consistent event payloads for navigation intents (`back`, `review`, `cancel`) so automation remains deterministic.

### 3. Accessibility and Compliance
- Require each bridge to respect high-contrast and colour-blind themes defined in the CLI configuration.
- Capture keyboard shortcut mappings for navigation, confirmation, and cancellation, ensuring parity between CLI, Textual, and WebUI.
- Define logging expectations so transcripts and layout snapshots can be audited regardless of the active bridge.

### 4. Integration Points
- Provide reference adapters for Typer (`CLIUXBridge`), prompt-toolkit (`PromptToolkitSession`), Textual (`TextualUXBridge`), and NiceGUI (`NiceGUIBridge`).
- Maintain an integration test matrix verifying that each bridge satisfies functional requirements FR-90 through FR-93 and existing WebUI obligations.

## Acceptance Criteria

1. The `UXBridge` interface defines capability negotiation and extended method signatures documented in developer guides and enforced by shared unit tests.
2. CLI, Textual, and WebUI bridges expose identical navigation semantics (back, next, review) with consistent logging and sanitisation behaviour.
3. Accessibility themes and keyboard shortcut conventions match across bridges, with documentation updated in the user guide.
4. Behaviour-driven scenarios demonstrate that workflows can switch bridges without altering orchestration logic or test fixtures.

## References

- [System Requirement FR-90 – FR-93](../system_requirements_specification.md#311-multi-channel-user-experience)
- [Specification: CLI UX Enhancements](cli-ux-enhancements.md)
- [Specification: Requirements Wizard Navigation](requirements-wizard-navigation.md)
- [Architecture Diagram: CLI/Textual UXBridge](../architecture/cli_textual_uxbridge.md)
- [BDD: shared_uxbridge_across_cli_and_webui.feature](../../tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature)
