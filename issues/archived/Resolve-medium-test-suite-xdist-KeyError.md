# Issue 145: Resolve medium test suite xdist KeyError
Milestone: 0.1.0-alpha.1 (completed 2025-02-19)
Status: closed
Priority: high
Dependencies: None

## Progress
- `poetry run devsynth run-tests --speed=medium` raised KeyError `<WorkerController gw2>` with 889 failing tests and 104 errors.
- 2025-02-14: `poetry run pytest -n auto --dist load` reproduced the failure; investigation identified leaked coverage collectors causing worker shutdowns.
- Patched `tests/conftest.py` to clean coverage state and integrate global-state reset. Medium suite now passes under xdist.
- Follow-up issue: [Investigate xdist worker timeouts](../Investigate-xdist-worker-timeouts.md).

## References
- [scripts/run_tests.sh](../../scripts/run_tests.sh)
