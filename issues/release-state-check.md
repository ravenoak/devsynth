# Release state check
Milestone: 0.1.0-beta.1
Status: ready for review
Priority: medium
Dependencies: docs/specifications/release-state-check.md, tests/behavior/features/release_state_check.feature

## Problem Statement
Release state check is not yet implemented, limiting DevSynth's release governance.

## Action Plan
- Review `docs/specifications/release-state-check.md` for requirements.
- Implement the feature to satisfy the requirements.
- Add or update BDD tests in `tests/behavior/features/release_state_check.feature`.
- Update documentation as needed.

## Progress
- 2025-09-09: extracted from dialectical audit backlog.
- 2025-09-12: Reviewed specification and existing BDD feature; implementation and step definitions pending.
- 2025-09-12: Implemented release-state check script with passing and failing scenarios.
- 2025-09-20: Reopened — unit coverage for `scripts/verify_release_state.py` (69.23 %) is recorded in `issues/tmp_cov_release_state.json`, but the BDD scenarios still fail because `tests/behavior/steps/release_state_steps.py` lacks the required imports. Follow docs/tasks.md §19.3.2 to restore the behavior harness before closing.【F:docs/implementation/release_state_check_invariants.md†L1-L74】【d43747†L1-L17】【4a11c5†L1-L32】【F:issues/tmp_cov_release_state.json†L1-L1】
- 2025-09-21: Restored the release-state BDD steps with stable imports, captured the passing behavior log, and promoted the invariants note to review.【F:tests/behavior/steps/release_state_steps.py†L1-L53】【F:test_reports/release_state_check_bdd.log†L1-L20】【F:docs/implementation/release_state_check_invariants.md†L1-L58】

## References
- Specification: docs/specifications/release-state-check.md
- BDD Feature: tests/behavior/features/release_state_check.feature
- Proof: see 'What proofs confirm the solution?' in [docs/specifications/release-state-check.md](../docs/specifications/release-state-check.md) and scenarios in [tests/behavior/features/release_state_check.feature](../tests/behavior/features/release_state_check.feature).
