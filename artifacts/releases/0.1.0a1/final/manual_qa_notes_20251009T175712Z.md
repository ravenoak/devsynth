# Manual QA Notes — 2025-10-09 UAT Sweep

## Context
- Triggered after verifying go-task availability; environment still relies on Poetry 2.2.1 with the committed lock file.
- Objective: rerun maintainer UAT triad (`task release:prep`, `poetry run devsynth doctor`) before documenting readiness updates in issues/docs.
- Post-PR B follow-up on 2025-10-10 re-executed the triad to validate the normalized lockfile and capture the new smoke failure signature.【F:diagnostics/task_release_prep_20251010T025617Z.log†L1-L41】

## Execution Summary
| Command | Result | Evidence | Notes |
| --- | --- | --- | --- |
| `task release:prep` | ❌ Failed | [diagnostics/task_release_prep_20251010T025617Z.log](task_release_prep_20251010T025617Z.log) | Workflow now clears Poetry install and both build steps before pytest-bdd raises `IndexError: list index out of range` while resolving `bdd_features_base_dir`; smoke abort leaves triad incomplete. |
| `poetry run devsynth doctor` | ⏳ Pending | [diagnostics/devsynth_doctor_20251009T175659Z.log](devsynth_doctor_20251009T175659Z.log) | Not reattempted on 2025-10-10 because `release:prep` failed during smoke collection; last captured log still shows `ModuleNotFoundError` from the pre-fix environment. |

## Socratic Review — PR B Follow-up (2025-10-10)

### Problem: Did the lockfile repairs in PR B unblock Poetry so UAT can progress?
- `task release:prep` now reports "No dependencies to install or update" before continuing with the wheel/sdist build, confirming the lockfile parses successfully during the maintainer workflow.【F:diagnostics/task_release_prep_20251010T025617Z.log†L1-L30】
- The dedicated transcript for the refreshed `poetry install --with dev --extras "tests retrieval chromadb api"` run finishes with `Status: success`, validating that Poetry 2.2.1 can reinstall the project after the metadata cleanup.【F:diagnostics/poetry_install_with_dev_tests_retrieval_chromadb_api_20251010T025311Z.log†L1-L40】【F:diagnostics/poetry_install_with_dev_tests_retrieval_chromadb_api_20251010T025311Z.log†L41-L60】

### Proof: The triad advances farther than the 2025-10-09 sweep.
- The 2025-10-10 `release:prep` attempt proceeds through environment checks, dependency installation, and package builds before pytest collection fails on a `bdd_features_base_dir` lookup, demonstrating progress beyond the prior lockfile error.【F:diagnostics/task_release_prep_20251010T025617Z.log†L1-L41】
- Manual QA evidence now captures both the successful install transcript and the updated failure mode so release documentation can cite the new state instead of the earlier `<empty>` constraint regression.【F:diagnostics/poetry_install_with_dev_tests_retrieval_chromadb_api_20251010T025311Z.log†L1-L60】【F:diagnostics/task_release_prep_20251010T025617Z.log†L31-L41】

### Problem: What still blocks UAT sign-off after PR B?
- Pytest-bdd aborts during the smoke subset invoked by `task release:prep`, leaving the maintainer triad red even though dependency installation and builds now succeed.【F:diagnostics/task_release_prep_20251010T025617Z.log†L31-L41】
- Because the workflow stops at smoke collection, the dedicated `poetry run devsynth doctor` verification remains outstanding and must be rerun once the BDD configuration is restored.【F:diagnostics/task_release_prep_20251010T025617Z.log†L31-L41】

## Follow-up Actions
1. Patch the pytest-bdd configuration so `scenarios()` finds the configured features base directory during smoke collection.【F:diagnostics/task_release_prep_20251010T025617Z.log†L31-L41】
2. Re-run `task release:prep` once the smoke subset is stable, then capture a fresh `poetry run devsynth doctor` log to complete the maintainer triad evidence bundle.【F:diagnostics/task_release_prep_20251010T025617Z.log†L31-L41】
3. Update release readiness documentation and issues with the passing transcripts, keeping workflows on `workflow_dispatch` until maintainers confirm the repaired gates and tag `v0.1.0a1`.
