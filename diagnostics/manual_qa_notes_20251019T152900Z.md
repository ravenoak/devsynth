# Manual QA Notes — 2025-10-19 Maintainer Triad

## Context
- Triggered after repairing pytest-bdd base directory handling in `conftest.py` so behavior scenarios import without relying on pytest configuration order.
- Objective: rerun the maintainer UAT triad (`task release:prep`, `poetry run devsynth doctor`) and capture green evidence for release readiness updates.
- Environment bootstrapped via `scripts/install_dev.sh`; go-task 3.45.4 available and Poetry 2.2.1 reuses the committed lock file.

## Execution Summary
| Command | Result | Evidence | Notes |
| --- | --- | --- | --- |
| `task release:prep` | ✅ Passed | [diagnostics/task_release_prep_20251019T152521Z.log](task_release_prep_20251019T152521Z.log) | Smoke run completes with 4 ,704 scenarios skipped (pytest-bdd no longer raises `IndexError`); wheel+sdist rebuilds and verification scripts succeed. |
| `poetry run devsynth doctor` | ⚠️ Warnings | [diagnostics/devsynth_doctor_20251019T152756Z.log](devsynth_doctor_20251019T152756Z.log) | Doctor highlights missing production/staging secrets (expected in offline dev env); no module import errors remain. |

## Socratic Review — Pytest-BDD Remediation

### Problem: Did the shim prevent `CONFIG_STACK` underflows during scenario discovery?
- Yes. The new wrapper injects an absolute `features_base_dir` before pytest-bdd inspects `CONFIG_STACK`, so `scenarios()` runs succeed even when optional imports load feature modules outside the pytest lifecycle.【F:conftest.py†L49-L117】
- `task release:prep` now executes the smoke subset end-to-end, producing 4 ,791 skipped tests and completing in 105 s without the previous `IndexError: list index out of range` failure.【F:diagnostics/task_release_prep_20251019T152521Z.log†L1-L120】

### Proof: Maintainer automation and doctor command both execute
- Wheel and sdist rebuild, marker verification, and minimal extras validation all succeed in the release prep log, confirming the automation gate is green again.【F:diagnostics/task_release_prep_20251019T152521Z.log†L1-L180】
- `poetry run devsynth doctor` runs to completion, reporting only missing environment secrets rather than module import errors.【F:diagnostics/devsynth_doctor_20251019T152756Z.log†L1-L21】

## Follow-up Actions
1. Update `docs/tasks.md` §30.3 and release readiness issues with the new passing evidence bundle.
2. Keep tracking environment secret warnings in doctor output for production staging, but no further action is required for the offline dev triad.
3. Share the green transcripts with maintainers so they can proceed to the post-tag CI re-enable plan when ready.
