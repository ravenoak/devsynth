# Verify test markers script failures
Milestone: Phase 2
Status: open
Priority: high
Dependencies: scripts/verify_test_markers.py, test_markers_report.json

## Problem Statement
The `scripts/verify_test_markers.py` guard fails for several test modules, reporting unrecognized markers when parameterized tests increase the collected count. This indicates inconsistent or missing speed markers and blocks the verification pipeline.

## Action Plan
- Analyze files listed in `test_markers_report.json` to identify causes of count mismatches.
- Ensure each test function carries exactly one `fast`, `medium`, or `slow` marker.
- Adjust `scripts/verify_test_markers.py` to account for parameterized tests or update affected tests.
- Re-run marker verification and regenerate the report.

## Progress
- 2025-08-20: Verified script fails with multiple `unrecognized_markers` entries.
- 2025-08-20: Updated script to account for parametrized tests, normalized markers, and regenerated report.

## References
- scripts/verify_test_markers.py
- test_markers_report.json
