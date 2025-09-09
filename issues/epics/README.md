# DevSynth Epics Overview (0.1.0a1)

This document consolidates related issues into epics with clear dependencies and milestones to support the 0.1.0a1 readiness goals. It aligns with
- project guidelines (SDD, TDD, BDD; clarity and maintainability)
- docs/roadmap/release_plan.md (version, milestones)

Use this as the umbrella index to track progress and burndown across the most impactful workstreams.

## Conventions
- Epic = a curated group of related issues with a milestone and dependency graph
- Each epic lists: objective, scope, dependencies, deliverables, milestone, and links to specs/tests
- Status tags: [planned] [in-progress] [blocked] [done]
- Traceability: link specs under docs/specifications and tests under tests/* when applicable

---

## Epic: WSDE/EDRR Workflow Finalization [in-progress]
Objective: Finalize WSDE/EDRR workflow logic and integrate Sprint-EDRR, ensuring consensus phases align with EDRR transitions and BDD coverage.

Scope:
- Define/clarify transitions, consensus hooks, failure handling
- Implement missing step definitions for BDD features
- Align documentation and examples

Dependencies:
- issues/Finalize-WSDE-EDRR-workflow-logic.md
- issues/Complete-Sprint-EDRR-integration.md
- docs/specifications/finalize-wsde-edrr-workflow-logic.md
- docs/specifications/complete-sprint-edrr-integration.md
- tests/behavior/ (EDRR/WSDE related features and steps)

Deliverables:
- Updated EDRR workflow logic and Sprint integration
- Passing BDD scenarios with step definitions
- Documentation updates reflecting transitions/consensus phases

Milestone: 0.1.0a1 (critical path: unblock release prep if scenarios are required by CI)

---

## Epic: Memory Backends Integration Hardening [planned]
Objective: Harden and align memory backends (LMDB/FAISS/Kuzu/ChromaDB) with consistent interfaces and robust transactions/sync.

Scope:
- Sync manager finalization across LMDB/FAISS/Kuzu
- ChromaDB transaction/error handling
- Cross-store sync integration tests (persistence, retrieval)

Dependencies:
- issues/Complete-memory-system-integration.md
- docs/specifications/complete-memory-system-integration.md
- tests/integration/ and tests/behavior/ memory scenarios

Deliverables:
- Stable interfaces and sync manager
- Expanded integration tests for persistence/retrieval/sync
- Graceful handling for minimal installs (already covered; verify)

Milestone: 0.1.0a1 (carry over remaining parts to 0.1.0a2 if needed)

---

## Epic: Cross-Interface CLI/UX Parity and Consistency [planned]
Objective: Ensure consistent behavior and formatted/sanitized outputs across CLI, API, and WebUI bridges.

Scope:
- Cross-interface consistency features and edge cases
- Output sanitization/format standardization
- Friendly messaging for missing extras/backends (baseline complete; extend tests)

Dependencies:
- issues/cross-interface-consistency.md
- issues/extended-cross-interface-consistency.md
- issues/archived/CLI-and-UI-improvements.md (historical context)
- docs/specifications/cross-interface-consistency.md
- docs/specifications/extended-cross-interface-consistency.md
- tests/behavior/features/*cross_interface* and related unit/integration tests

Deliverables:
- Documented standards for output formatting and sanitization
- Tests validating parity and resilience

Milestone: 0.1.0a1 (tests may continue into 0.1.0a2)

---

## Burndown and Tracking
- Milestone: v0.1.0a1 (see docs/roadmap/release_plan.md)
- Suggested metrics: number of open issues per epic, completed checkboxes in docs/tasks.md per related items, scenario pass-rate per feature group
- Reporting cadence: update this README and docs/tasks.md when a related issue reaches done

## Epic Template (for new epics)
```
## Epic: <Title> [planned|in-progress|blocked|done]
Objective: <What outcome and why>
Scope:
- <Bullet points>
Dependencies:
- <Issues>
- <Specs>
- <Tests>
Deliverables:
- <Bullet points>
Milestone: <version>
```
