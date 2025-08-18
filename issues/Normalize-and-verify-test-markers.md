# Normalize and verify test markers
Milestone: 0.1.0-alpha.1
Status: in progress
Priority: high
Dependencies: None


The test suite must ensure each test file contains exactly one speed marker (`fast`, `medium`, or `slow`). Some tests may lack markers, have duplicates, or include outdated placement. High-memory tests must be gated with `memory_intensive`.

## Plan
1. Generate baseline marker report:
   - `poetry run python [scripts/verify_test_markers.py](../scripts/verify_test_markers.py)` to identify missing or duplicate markers.
2. Normalize markers:
   - `poetry run python [scripts/add_missing_markers.py](../scripts/add_missing_markers.py)` for unmarked tests.
   - `poetry run python [scripts/fix_duplicate_markers.py](../scripts/fix_duplicate_markers.py)` for duplicated markers.
   - `poetry run python [scripts/standardize_marker_placement.py](../scripts/standardize_marker_placement.py)` to enforce consistent placement.
   - Apply `poetry run python [scripts/fix_all_test_markers.py](../scripts/fix_all_test_markers.py)` for any bulk cleanup.
3. Flag resource-heavy tests:
   - Gate high-memory tests with `@pytest.mark.memory_intensive` or refactor to lighter fixtures.
4. Verify:
   - Re-run `poetry run python [scripts/verify_test_markers.py](../scripts/verify_test_markers.py)` to confirm all files contain exactly one speed marker.
   - Run `poetry run devsynth run-tests --speed=fast` followed by `--speed=medium` and `--speed=slow` to validate marker filtering.
5. Document:
   - Update contributing guidelines if marker requirements change.
   - Track progress in issue updates.

## Progress
- 2025-02-19: script still hangs around 150 files; investigation continuing.

- Initial verification attempt timed out; needs further investigation.
- A second run after provisioning also hung and required manual interruption.
- Third attempt after refining the environment provisioning to avoid heavy GPU extras still hung, indicating an internal issue with `verify_test_markers.py`.
- Updated `verify_test_markers.py` and supporting utilities to handle direct script execution, but verification still hangs and requires manual interruption ([dcc3a755](../commit/dcc3a755)).
- Latest run with `--workers 1` continues to hang and needs manual termination.
- Recent attempt after environment preparation still hung after several minutes and required manual interruption.
- Marker normalization blocks [Resolve pytest-xdist assertion errors](Resolve-pytest-xdist-assertion-errors.md).
- Reproduced the hang on a minimal test set by running `poetry run python scripts/verify_test_markers.py --workers 1 tests/unit/interface/test_bridge_conformance.py`; logging revealed blocking during the `pytest --collect-only` subprocess call, so the script now logs subprocess start/end and exits non-zero when issues persist.
- 2025-08-16: Re-running `poetry run python scripts/verify_test_markers.py` after executing the environment provisioning script still hangs and requires manual interruption.
- 2025-08-16: Latest attempt processed 150 of 679 files (~18s) before hanging, confirming persistent blocking in `pytest --collect-only`.
- 2025-08-17: Running `poetry run python scripts/verify_test_markers.py --workers 1` processed 50 of 700 files (~76s) before hanging and required manual interruption.
- 2025-08-17: Executed `standardize_marker_placement.py`, which updated hundreds of files but introduced syntax errors, so changes were reverted; marker verification still hangs.
- 2025-08-18: Another run of `poetry run python scripts/verify_test_markers.py` after environment provisioning hung without completing and was manually interrupted, producing only a start message in the log.

## References

- Related: [Resolve pytest-xdist assertion errors](Resolve-pytest-xdist-assertion-errors.md)
- Related: [Expand test generation capabilities](Expand-test-generation-capabilities.md)
