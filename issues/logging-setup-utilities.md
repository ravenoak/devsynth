# Logging Setup Utilities
Milestone: 0.1.0-beta.1
Status: in progress
Priority: medium
Dependencies: docs/specifications/logging_setup.md, tests/behavior/features/logging_setup.feature

## Problem Statement
Logging Setup Utilities are not yet implemented, limiting DevSynth's diagnostic capabilities.

## Action Plan
- Review `docs/specifications/logging_setup.md` for requirements.
- Implement the feature to satisfy the requirements.
- Add or update BDD tests in `tests/behavior/features/logging_setup.feature`.
- Update documentation as needed.

## Progress
- 2025-09-09: extracted from dialectical audit backlog.
- 2025-09-17: Validated handler wiring and environment toggles via `tests/unit/logging/test_logging_setup_contexts.py::{test_cli_context_wires_console_and_json_file_handlers,test_test_context_redirects_and_supports_console_only_toggle,test_create_dir_toggle_disables_json_file_handler}` (seed: deterministic/no RNG).
- 2025-09-20: Invariant note promoted to review with targeted coverage (41.15 % line coverage for `logging_setup.py`) captured in `issues/tmp_cov_logging_setup.json`; spec updated to cross-link the unit suites and published evidence.【F:docs/implementation/logging_invariants.md†L1-L66】【F:docs/specifications/logging_setup.md†L1-L40】【F:issues/tmp_cov_logging_setup.json†L1-L1】

## References
- Specification: docs/specifications/logging_setup.md
- BDD Feature: tests/behavior/features/logging_setup.feature
- Proof: see 'What proofs confirm the solution?' in [docs/specifications/logging_setup.md](../docs/specifications/logging_setup.md) and scenarios in [tests/behavior/features/logging_setup.feature](../tests/behavior/features/logging_setup.feature).
