# DevSynth run-tests hangs
Milestone: 0.1.0-alpha.1
Status: todo
Priority: high
Dependencies: release-readiness-v0-1-0-alpha-1.md, Resolve-pytest-xdist-assertion-errors.md

## Problem Statement
Executing `poetry run devsynth run-tests --speed fast` or `pytest -m fast` hangs without producing output, preventing validation of the test suite. This blocks the release process and undermines confidence in automated testing.

## Action Plan
- Reproduce the hang with `devsynth run-tests` and `pytest` to capture diagnostics.
- Ensure optional providers default to disabled to avoid stalls.
- Investigate subprocess usage in `run_tests` for blocking behavior.
- Add regression tests to confirm `devsynth run-tests` completes and reports results.
- Update documentation on running tests once the issue is resolved.

## Progress
- 2025-08-23: Initial report—commands hang on fresh environment; `scripts/verify_test_markers.py` completes, indicating tests exist but runner stalls.

## References
- issues/release-readiness-v0-1-0-alpha-1.md
- issues/Resolve-pytest-xdist-assertion-errors.md
