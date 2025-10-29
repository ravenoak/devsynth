---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-08-19
status: draft
tags:

- specification

title: Complete Sprint-EDRR integration
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
Integrate Agile sprint ceremonies with the Expand, Differentiate, Refine,
Retrospect (EDRR) cycle so that planning and review artifacts are keyed to
their corresponding phases.

## Socratic Checklist
- What is the problem?
  - Sprint planning and review data lack a direct mapping to EDRR phases.
- What proofs confirm the solution?
  - Helper functions map ceremonies to phases and BDD scenarios exercise the
    alignment.

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/complete_sprint_edrr_integration.feature`](../../tests/behavior/features/complete_sprint_edrr_integration.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

Teams using sprints need a lightweight way to translate planning scope and
review feedback into EDRR outputs so DevSynth's tooling can reason about
them consistently.

## Specification
1. `CEREMONY_PHASE_MAP` defines default mappings:
   - planning → Expand
   - standups → Differentiate
   - review → Refine
   - retrospective → Retrospect
2. `align_sprint_planning(planning_sections)` returns a dictionary keyed by
   `Phase` for any planning sections with known ceremonies.
3. `align_sprint_review(review_sections)` mirrors the planning helper for
   review feedback.
4. Unknown ceremonies are ignored, allowing custom extensions without
   impacting core behavior.

## Acceptance Criteria
- Given planning sections for "planning" and "review", the alignment
  produces entries for the Expand and Refine phases.
- Given review feedback for the "review" ceremony, the alignment maps data to
  the Refine phase and skips unmapped ceremonies.

## References

- [Issue: Complete Sprint-EDRR integration](../../issues/Complete-Sprint-EDRR-integration.md)
- [BDD: complete_sprint_edrr_integration.feature](../../tests/behavior/features/complete_sprint_edrr_integration.feature)
