# Manual QA Notes — 2025-10-09 UAT Sweep

## Context
- Triggered after verifying go-task availability; environment still relies on Poetry 2.2.1 with the committed lock file.
- Objective: rerun maintainer UAT triad (`task release:prep`, `poetry run devsynth doctor`) before documenting readiness updates in issues/docs.

## Execution Summary
| Command | Result | Evidence | Notes |
| --- | --- | --- | --- |
| `task release:prep` | ❌ Failed | [diagnostics/task_release_prep_20251009T175608Z.log](task_release_prep_20251009T175608Z.log) | Poetry aborts with `Could not parse version constraint: <empty>` while reading the lock file. Failure reproduces prior bootstrap script error; no artifacts beyond the log were generated. |
| `poetry run devsynth doctor` | ❌ Failed | [diagnostics/devsynth_doctor_20251009T175659Z.log](devsynth_doctor_20251009T175659Z.log) | CLI cannot import `devsynth` because the package isn't installed; Poetry warns about running uninstalled entry points. Indicates `poetry install` still required once lock parsing issue is solved. |

## Observations
- Both failures block completion of the UAT evidence bundle; they align with outstanding tasks in docs/tasks §30.3–§30.4.
- Diagnostics from `bash scripts/install_dev.sh` earlier in the session confirm Poetry install bootstrap fails with the same version constraint parsing error (see [diagnostics/poetry_install_mandatory-bootstrap_attempt1_20251009T175505Z.log](poetry_install_mandatory-bootstrap_attempt1_20251009T175505Z.log)).
- Next remediation step is to audit `poetry.lock` (and any extras metadata) for malformed entries so Poetry 2.2.1 can install dependencies; until then, UAT gates remain red.

## Follow-up Actions
1. Investigate the empty version constraint in `poetry.lock`; adjust dependency metadata or pin Poetry to a known-good version if necessary.
2. Re-run `poetry install --with dev --extras "tests retrieval chromadb api"` once the lock issue is resolved.
3. Repeat `task release:prep` and `poetry run devsynth doctor`, updating the release issues with green evidence when available.
4. Keep workflows on `workflow_dispatch` until maintainers confirm the gate repairs and tag `v0.1.0a1`.

