# Consolidate `artifacts/` and `diagnostics/` structure and policies
Milestone: 0.1.x
Status: Proposed
Priority: Medium
Dependencies: docs/policies/artifacts_and_diagnostics_policy.md

## Problem Statement
Evidence and logs are scattered across `artifacts/` and `diagnostics/` with inconsistent structure and naming, making it harder to audit and automate retention.

## Action Plan
- Add/Update READMEs describing canonical layouts and conventions.
- Move research artefacts under `artifacts/research/` (non-breaking via `git mv`).
- Create subfolders under `diagnostics/` for linting, typing, testing, security, and doctor. Stage non-destructive moves in follow-ups.
- Update documentation and link from AGENTS.md and docs/tasks.md.

## Acceptance Criteria
- READMEs present and clear; policy doc added under `docs/policies/`.
- Tracking plan for relocating existing files without data loss.
- CI and developer guides reference new structure.

## References
- `artifacts/README.md`
- `diagnostics/README.md`
- `docs/policies/artifacts_and_diagnostics_policy.md`
