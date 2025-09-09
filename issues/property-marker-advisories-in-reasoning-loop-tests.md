Title: Missing property markers in reasoning loop property tests
Date: 2025-09-09 00:57 UTC
Status: open
Affected Area: tests
Reproduction:
  - poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
Exit Code: 0
Artifacts:
  - test_markers_report.json
  - /tmp/markers.log
Suspected Cause: tests/property/test_reasoning_loop_properties.py::check lacks @pytest.mark.property and a speed marker.
Next Actions:
  - [ ] Add required markers to tests/property/test_reasoning_loop_properties.py::check.
  - [ ] Re-run verify_test_markers.py to confirm 0 property_violations.
Resolution Evidence:
  - (pending)
