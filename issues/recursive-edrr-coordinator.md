# Recursive EDRR Coordinator
Milestone: 0.1.0
Status: in progress
Priority: low
Dependencies: Phase-2-completion.md, docs/specifications/recursive-edrr-coordinator.md, tests/behavior/features/recursive_edrr_coordinator.feature

## Problem Statement
Recursive EDRR Coordinator is not yet implemented, limiting DevSynth's capabilities.


## Action Plan
- Review `docs/specifications/recursive-edrr-coordinator.md` for requirements.
- Implement the feature to satisfy the requirements.
- Add or update BDD tests in `tests/behavior/features/recursive_edrr_coordinator.feature`.
- Update documentation as needed.

## Progress
- 2025-02-19: extracted from dialectical audit backlog.
- 2025-09-21: Restored `devsynth.application.edrr.templates` registration within the coordinator, added threshold helper unit tests, and promoted `docs/implementation/edrr_invariants.md` to review (see docs/tasks.md §26.8).
- 2025-09-22: Replaced direct PromptManager imports with the `SupportsTemplateRegistration` protocol, added `test_coordinator_registers_templates` to `tests/unit/application/edrr/test_threshold_helpers.py`, and published `docs/implementation/edrr_invariants.md` with updated evidence.

## References
- Specification: docs/specifications/recursive-edrr-coordinator.md
- BDD Feature: tests/behavior/features/recursive_edrr_coordinator.feature
- Proof: see 'What proofs confirm the solution?' in [docs/specifications/recursive-edrr-coordinator.md](../docs/specifications/recursive-edrr-coordinator.md) and scenarios in [tests/behavior/features/recursive_edrr_coordinator.feature](../tests/behavior/features/recursive_edrr_coordinator.feature).
