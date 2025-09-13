Title: Release blockers for 0.1.0a1
Date: 2025-09-12 00:00 UTC
Status: closed
Affected Area: release
Reproduction:
  - N/A (planning issue)
Exit Code: N/A
Artifacts:
  - N/A
Suspected Cause: Outstanding features and tests prevent tagging v0.1.0a1.
Next Actions:
  - [x] Implement release state check feature (docs/specifications/release-state-check.md).
  - [x] Add BDD coverage for high-priority specs listed in issues/missing-bdd-tests.md.
  - [x] Review components for missing proofs or simulations and document gaps.
  - [x] Confirm all GitHub Actions workflows remain dispatch-only until release.
  - [x] Investigate fast+medium coverage run failure (`ERROR unit/general/test_test_first_metrics.py`) and ensure coverage artifact generation.
Progress:
- 2025-09-12: Restored `devsynth` CLI and `task` via `poetry install --with dev --all-extras` and `bash scripts/install_dev.sh`; smoke tests and verification scripts pass. Coverage aggregation and release state check remain pending.
- 2025-09-12: Investigated coverage run failure and regenerated htmlcov/, coverage.json, and docs/coverage.svg.
- 2025-09-13: Release state check and BDD coverage implemented; proofs documented; workflows confirmed dispatch-only. Issue closed after smoke tests and verification scripts passed.
Resolution Evidence:
  - docs/tasks.md item 18
