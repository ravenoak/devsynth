Title: Release blockers for 0.1.0a1
Date: 2025-09-12 00:00 UTC
Status: open
Affected Area: release
Reproduction:
  - N/A (planning issue)
Exit Code: N/A
Artifacts:
  - N/A
Suspected Cause: Outstanding features and tests prevent tagging v0.1.0a1.
Next Actions:
  - [ ] Implement release state check feature (docs/specifications/release-state-check.md).
  - [ ] Add BDD coverage for high-priority specs listed in issues/missing-bdd-tests.md.
  - [ ] Review components for missing proofs or simulations and document gaps.
  - [ ] Confirm all GitHub Actions workflows remain dispatch-only until release.
  - [ ] Investigate fast+medium coverage run failure (`ERROR unit/general/test_test_first_metrics.py`) and ensure coverage artifact generation.
Resolution Evidence:
  -
