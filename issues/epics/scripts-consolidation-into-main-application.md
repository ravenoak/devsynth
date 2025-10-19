# Consolidate `scripts/` into main application (Epic)
Milestone: 0.1.x
Status: Proposed
Priority: High
Dependencies: validate-metadata-command.md; validate-manifest-command.md; unified-test-cli-implementation.md; testing-script-consolidation.md

## Problem Statement
The repository contains a large number of Python and shell scripts in `scripts/` that duplicate or partially overlap with built-in CLI capabilities under `src/devsynth/application/cli/`. This fragmentation causes:
- Divergent UX and duplicated options/flags across entry points
- Hard-to-maintain validation flows (some logic only exists in scripts)
- Confusion between CI-only guards and end-user commands

We need to merge reusable functionality into the primary application (CLI modules and internal libraries), keep CI-only checks where appropriate, and deprecate wrapper scripts with clear migration paths.

## Goals
- Provide a single coherent CLI surface for common operations: testing, security audit, doctor checks, configuration validation, documentation validation, and traceability.
- Migrate script-only logic into application modules with tests and documentation.
- Deprecate and remove duplicate wrappers after a grace period (post `v0.1.0a1`).

## Non-Goals
- Rewriting one-off maintenance scripts that intentionally live outside the CLI (e.g., mass refactors and bespoke fixers) unless they become stable features.
- Changing CI policy or re-enabling workflow triggers before the `v0.1.0a1` tag (see AGENTS.md).

## Current State (Socratic inventory)
- Testing orchestration scripts: `run_unified_tests.py`, advanced test modes, prioritization, and distributed runners. The application already exposes `devsynth run-tests`; we should unify modes and flags there instead of invoking many scripts.
- Validation scripts: `validate_manifest.py` (already a wrapper), `validate_metadata.py` (has `validate_metadata_cmd` in app), `validate_config.py` (schema + env checks used indirectly by `doctor_cmd`).
- Security: `scripts/security/security_scan.py` runs Bandit/Safety with outputs; the CLI has `security-audit` but should align outputs/flags.
- Hygiene: `repo_hygiene_check.py` is not exposed in CLI; suitable as a `doctor` sub-check.
- Docs utilities: internal-links, index generation, breadcrumb dedupe; candidates for a `docs` command group.
- Traceability: `verify_requirements_traceability.py`, `verify_reqid_references.py`, `verify_docstring_reqids.py`; propose a `traceability` CLI.
- CI-only repo policy checks: numerous `verify_*` scripts. Keep as CI/dev tools; optionally group under a hidden or `--ci` mode later.

## Remediation Plan (Dialectical synthesis)
Phase 1 (Core parity and lowest-risk merges):
- Move `scripts/validate_config.py` logic into `src/devsynth/application/config_validation.py` (library module). Update `doctor_cmd` to import this directly (remove dynamic import of the script). Provide tests. Mark `scripts/validate_config.py` as deprecated with a thin wrapper (or remove after deprecation window).
- Integrate `repo_hygiene_check.py` into `doctor_cmd` (new sub-check). Add a flag to show offenders and exit non-zero when requested.
- Align `security_audit_cmd` with `scripts/security/security_scan.py` outputs and `--strict` semantics; persist `bandit.json` and `safety.json` at repo root; document env var support for Safety key.
- Introduce CLI commands for formatting and typing: `devsynth lint [--fix]` (Black+isort) and `devsynth typecheck` (mypy). Deprecate `run_style_checks.py` and `run_static_analysis.py`.
- Extend `devsynth run-tests` to support unified modes comparable to `run_unified_tests.py` (incremental, balanced, critical) via flags or a mode option, avoiding shelling to other scripts.

Phase 2 (Documentation and traceability consolidation):
- Add a `devsynth docs` command group with `validate-internal-links`, `generate-index`, `dedupe-breadcrumbs`, and `validate-metadata` (reusing existing `validate_metadata_cmd`). Migrate logic from scripts into library functions with tests.
- Add a `devsynth traceability` command group combining: requirements traceability check, docstring reqid validation, and reqid reference scan. Emit machine-readable artifacts in `test_reports/` (or `diagnostics/`) for CI.
- Clarify CI-only `verify_*` scripts as internal tooling and document them. Where overlapping with new commands, convert scripts to thin wrappers or retire them.

Phase 3 (Cleanup and deprecation removals):
- Remove deprecated wrappers once `v0.1.0a1` grace period passes. Update docs and `docs/tasks.md` to reference CLI commands exclusively.

## Acceptance Criteria
- Phase 1 PRs:
  - `doctor_cmd` imports and uses first-party config validation (no dynamic imports from `scripts/`).
  - `doctor_cmd` includes repo hygiene sub-check with actionable output.
  - `security-audit` produces `bandit.json` and `safety.json`; `--strict` exits non-zero on any vulnerabilities.
  - New commands `lint` and `typecheck` exist with parity to the scripts (including `--fix` for `lint`).
  - `run-tests` supports unified modes without invoking other scripts; documentation updated.
- Phase 2 PRs:
  - `docs` command group provides the listed subcommands and passes unit tests on core logic.
  - `traceability` command group validates matrix, docstrings, and references; outputs are consumable in CI.
  - Overlapping scripts are converted to wrappers or deprecated with clear messages.
- Phase 3 PRs:
  - Deprecated wrappers removed; references in docs updated.

## References
- `src/devsynth/application/cli/commands/*`
- `scripts/security/security_scan.py`, `scripts/repo_hygiene_check.py`, `scripts/validate_config.py`
- Existing issues: `testing-script-consolidation.md`, `unified-test-cli-implementation.md`, `validate-metadata-command.md`, `validate-manifest-command.md`
