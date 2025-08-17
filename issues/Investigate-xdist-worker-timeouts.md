# Investigate xdist worker timeouts
Milestone: 0.1.0-alpha.1
Status: open
Priority: medium
Dependencies: [Resolve pytest-xdist assertion errors](Resolve-pytest-xdist-assertion-errors.md), [Normalize and verify test markers](Normalize-and-verify-test-markers.md)

Running `poetry run devsynth run-tests` occasionally hangs with xdist workers timing out, especially during marker verification.

## Progress
- 2025-02-19: timeout reproduced during `scripts/verify_test_markers.py` run; root cause undetermined.

## References
- [scripts/verify_test_markers.py](../scripts/verify_test_markers.py)
