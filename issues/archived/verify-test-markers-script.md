# Verify test markers script failures
Milestone: 0.1.0-beta.1
Status: open
Priority: medium
Dependencies: scripts/verify_test_markers.py, test_markers_report.json

## Problem Statement
The `scripts/verify_test_markers.py` guard fails for several test modules, reporting unrecognized markers when parameterized tests increase the collected count. This indicates inconsistent or missing speed markers and blocks the verification pipeline.

## Action Plan
- Analyze files listed in `test_markers_report.json` to identify causes of count mismatches.
- Ensure each test function carries exactly one `fast`, `medium`, or `slow` marker.
- Adjust `scripts/verify_test_markers.py` to account for parameterized tests or update affected tests.
- Add persistent caching and an incremental `--changed` option to focus on modified tests.
- Handle missing optional dependencies gracefully to avoid collection crashes.
- Re-run marker verification and regenerate the report.

## Progress
- 2025-08-20: Verified script fails with multiple `unrecognized_markers` entries.
- 2025-08-20: Updated `verify_test_markers.py` to de-duplicate parametrized tests and
  normalized memory test modules with missing speed markers; regenerated report shows
  expected counts.
- 2025-08-21: Re-running `scripts/verify_test_markers.py` processed ~150 of 735 files in ~15s before manual interruption, indicating performance issues persist.
- 2025-08-22: Added caching, `--changed` incremental mode, and optional dependency handling; incremental runs finish in under 30s.

## Usage

Run incremental verification for changed tests only:

```
poetry run python scripts/verify_test_markers.py --changed
```

Cached collection results are stored in `.pytest_collection_cache.json` to speed up subsequent executions.

## References
- scripts/verify_test_markers.py
- test_markers_report.json
