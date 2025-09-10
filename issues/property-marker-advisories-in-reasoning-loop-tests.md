---
Title: property marker advisories in reasoning loop tests
Date: 2025-09-09
Status: closed
Affected Area: tests
Reproduction:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
Exit Code: 0 (property_violations=0)
Artifacts:
  - test_markers_report.json
Suspected Cause: verify_test_markers treats nested Hypothesis `@given` helpers named `check` as test functions, so they appear unmarked.
Next Actions:
  - [x] refine scripts/verify_test_markers.py to ignore nested Hypothesis helpers or mark those helpers explicitly
  - [x] re-run verify_test_markers and attach updated report
Resolution Evidence:
  - verify_test_markers now reports 0 property marker violations after ignoring nested @given helpers
---
