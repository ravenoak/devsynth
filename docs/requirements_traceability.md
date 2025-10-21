---
title: "Requirements Traceability Matrix"
date: "2025-09-29"
version: "0.1.0-alpha.1"
tags:
  - "requirements"
  - "traceability"
  - "testing"
  - "validation"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-10-21"
owner: "DevSynth Maintainers"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; Requirements Traceability Matrix
</div>

# Requirements Traceability Matrix

## Summary
- Functional requirements FR-41 through FR-43 for WSDE collaboration, role management, and dialectical reasoning now map directly to the refreshed WSDE specifications and their executable behaviour suites, closing the backlog noted in the plan.【F:docs/system_requirements_specification.md†L171-L173】【F:docs/specifications/wsde-peer-review-workflow.md†L1-L80】【F:docs/specifications/wsde-message-passing-and-peer-review.md†L1-L75】【F:docs/specifications/consensus-building.md†L1-L81】
- Behaviour-driven coverage exercises message passing, consensus voting, and dialectical peer review flows across the WSDE feature files, ensuring end-to-end traces for each requirement.【F:tests/behavior/features/wsde_peer_review_workflow.feature†L1-L87】【F:tests/behavior/features/wsde_voting_mechanisms_for_critical_decisions.feature†L1-L31】【F:tests/behavior/features/consensus_building.feature†L1-L15】
- Unit suites persist peer-review records, serialize consensus payloads, and detect conflicting opinions so the specifications have deterministic regression coverage backing the requirements.【F:tests/unit/domain/test_wsde_peer_review_workflow.py†L1-L40】【F:tests/unit/application/collaboration/test_peer_review_store.py†L1-L199】【F:tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py†L1-L38】【F:tests/unit/application/collaboration/test_wsde_team_consensus_utils.py†L1-L19】
- Verification for this update is archived in the diagnostics captured during the current session, including the fast+medium CLI attempt and the traceability check output.【F:diagnostics/devsynth_run_tests_fast_medium_20250929T233256Z.txt†L1-L27】【F:diagnostics/verify_requirements_traceability_20250929T233307Z.txt†L1-L1】
- Functional requirements FR-90 through FR-93 for prompt-toolkit enhanced prompts, Textual TUI navigation, and Rich summaries now map to updated CLI UX specifications and parity-focused BDD scenarios.【F:docs/specifications/cli-ux-enhancements.md†L33-L73】【F:docs/specifications/shared-uxbridge-across-cli-and-webui.md†L20-L58】【F:docs/specifications/requirements-wizard-navigation.md†L21-L55】【F:tests/behavior/features/cli_ux_enhancements.feature†L1-L33】【F:tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature†L1-L25】【F:tests/behavior/features/requirements_wizard_navigation.feature†L1-L26】

## WSDE collaboration requirements

| Requirement | Specification sources | Behaviour coverage | Unit coverage |
| --- | --- | --- | --- |
| FR-41 — Implement the WSDE model for agent organisation【F:docs/system_requirements_specification.md†L171-L171】 | WSDE message passing and peer review; WSDE peer review workflow【F:docs/specifications/wsde-message-passing-and-peer-review.md†L15-L65】【F:docs/specifications/wsde-peer-review-workflow.md†L15-L69】 | Peer review workflow scenarios covering routing, broadcast, priority, structured content, and revision loops【F:tests/behavior/features/wsde_peer_review_workflow.feature†L1-L87】 | Peer review workflow persistence across stores and review record storage tests【F:tests/unit/domain/test_wsde_peer_review_workflow.py†L1-L40】【F:tests/unit/application/collaboration/test_peer_review_store.py†L1-L199】 |
| FR-42 — Support role management in multi-agent collaboration【F:docs/system_requirements_specification.md†L172-L172】 | Consensus building specification outlining weighted voting and conflict resolution【F:docs/specifications/consensus-building.md†L15-L69】 | WSDE voting mechanisms and consensus features validating expertise-weighted decisions and fallback flows【F:tests/behavior/features/wsde_voting_mechanisms_for_critical_decisions.feature†L1-L31】【F:tests/behavior/features/consensus_building.feature†L1-L15】 | Consensus mixin utilities and conflict detection tests asserting opinion reconciliation logic【F:tests/unit/application/collaboration/test_wsde_team_consensus_utils.py†L1-L19】【F:tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py†L1-L38】 |
| FR-43 — Implement dialectical reasoning in collaboration【F:docs/system_requirements_specification.md†L173-L173】 | WSDE peer review workflow specification emphasising dialectical analysis in review cycles【F:docs/specifications/wsde-peer-review-workflow.md†L37-L70】 | Peer review feature scenario covering thesis/antithesis/synthesis feedback within WSDE teams【F:tests/behavior/features/wsde_peer_review_workflow.feature†L71-L78】 | Peer review store tests capturing reviewer notes and consensus metadata for dialectical artefacts【F:tests/unit/application/collaboration/test_peer_review_store.py†L126-L199】 |

## CLI and Wizard UX requirements

| Requirement | Specification sources | Behaviour coverage | Unit coverage |
| --- | --- | --- | --- |
| FR-90 — Enhance CLI prompts with prompt-toolkit history, completions, and multi-select while retaining fallbacks【F:docs/system_requirements_specification.md†L255-L255】 | CLI UX Enhancements: Prompt-Toolkit augmentation; Requirements Wizard Navigation input enhancements【F:docs/specifications/cli-ux-enhancements.md†L47-L60】【F:docs/specifications/requirements-wizard-navigation.md†L33-L45】 | CLI UX Enhancements feature validates history/completions and fallbacks【F:tests/behavior/features/cli_ux_enhancements.feature†L1-L33】 | Requirements collector unit tests maintain deterministic outputs as bridge capabilities expand【F:tests/unit/application/requirements/test_interactions.py†L1-L137】 |
| FR-91 — Provide keyboard navigation across wizard flows without sentinel commands【F:docs/system_requirements_specification.md†L256-L256】 | CLI UX Enhancements navigation guidance; Requirements Wizard Navigation finite-state model【F:docs/specifications/cli-ux-enhancements.md†L52-L55】【F:docs/specifications/requirements-wizard-navigation.md†L33-L55】 | Requirements Wizard Navigation scenarios cover shortcuts, summaries, and multi-select prompts【F:tests/behavior/features/requirements_wizard_navigation.feature†L1-L26】 | Requirements collector tests assert backtracking persistence with bridge adapters【F:tests/unit/application/requirements/test_interactions.py†L98-L137】 |
| FR-92 — Deliver a Textual-based TUI with multi-pane layout reusing UXBridge workflows【F:docs/system_requirements_specification.md†L257-L257】 | CLI UX Enhancements Textual shell; Shared UXBridge parity contract; CLI/Textual architecture diagram【F:docs/specifications/cli-ux-enhancements.md†L52-L55】【F:docs/specifications/shared-uxbridge-across-cli-and-webui.md†L20-L58】【F:docs/architecture/cli_textual_uxbridge.md†L20-L69】 | CLI UX Enhancements and Shared UXBridge features exercise Textual parity and orchestration consistency【F:tests/behavior/features/cli_ux_enhancements.feature†L27-L33】【F:tests/behavior/features/shared_uxbridge_across_cli_and_webui.feature†L1-L25】 | Textual bridge unit coverage pending; acceptance criteria require adapter tests during implementation【F:docs/specifications/cli-ux-enhancements.md†L69-L73】 |
| FR-93 — Render Rich-based structured summaries and help layouts for wizard outcomes【F:docs/system_requirements_specification.md†L258-L258】 | CLI UX Enhancements Rich layout section; Requirements Wizard Navigation contextual summary pane【F:docs/specifications/cli-ux-enhancements.md†L57-L60】【F:docs/specifications/requirements-wizard-navigation.md†L38-L55】 | Requirements Wizard Navigation scenarios verify live summary visibility during navigation【F:tests/behavior/features/requirements_wizard_navigation.feature†L16-L20】 | Layout snapshot tests to be introduced alongside Rich refactor per acceptance criteria【F:docs/specifications/cli-ux-enhancements.md†L69-L73】 |
## Audit artefacts
- `diagnostics/devsynth_run_tests_fast_medium_20250929T233256Z.txt` — captured the fast+medium CLI attempt showing the missing `devsynth` entry point so bootstrap remediation can be tracked alongside requirement verification.【F:diagnostics/devsynth_run_tests_fast_medium_20250929T233256Z.txt†L1-L27】
- `diagnostics/verify_requirements_traceability_20250929T233307Z.txt` — proof that the requirements traceability script recognised the refreshed WSDE specifications in this update.【F:diagnostics/verify_requirements_traceability_20250929T233307Z.txt†L1-L1】
