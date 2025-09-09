---
Title: property marker advisories in reasoning loop tests
Date: 2025-09-09
Status: open
Affected Area: tests
Reproduction:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
Exit Code: 0
Artifacts:
  - test_markers_report.json
Suspected Cause: tests/property/test_reasoning_loop_properties.py lacked @pytest.mark.property, causing verify_test_markers warnings.
Next Actions:
  - [ ] add missing marker and single speed marker
  - [ ] re-run verify_test_markers
Resolution Evidence:
  - pending
---
