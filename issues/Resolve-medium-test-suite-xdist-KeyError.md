# Resolve medium test suite xdist KeyError
Milestone: 0.1.0-alpha.1
Status: open

Priority: high
Dependencies: None

## Progress
- `poetry run devsynth run-tests --speed=medium` raised KeyError `<WorkerController gw2>` with 889 failing tests and 104 errors.

## References
- [scripts/run_tests.sh](../scripts/run_tests.sh)
