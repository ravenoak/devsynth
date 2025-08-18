# Issue 150: Investigate xdist worker timeouts
Milestone: 0.1.0-alpha.1 (completed 2025-08-17)
Status: closed
Priority: medium
Dependencies: [Resolve pytest-xdist assertion errors](../Resolve-pytest-xdist-assertion-errors.md), [Normalize and verify test markers](../Normalize-and-verify-test-markers.md)

Running `poetry run devsynth run-tests` occasionally hangs with xdist workers timing out, especially during marker verification.

## Progress
- 2025-02-19: timeout reproduced during `scripts/verify_test_markers.py` run; root cause undetermined.
- 2025-08-17: `poetry run python scripts/verify_test_markers.py --workers 1` still hung after processing 50 of 700 files (~76s), indicating worker timeouts remain unresolved.
- 2025-08-17: added subprocess timeout handling and worker spawn/termination logging; `scripts/verify_test_markers.py` completes with both `--workers 1` and default parallel settings.

## References
- [scripts/verify_test_markers.py](../scripts/verify_test_markers.py)
