# Resolve pytest-xdist assertion errors
Milestone: 0.1.0-alpha.2
Status: in progress

Priority: high
Dependencies: None

## Problem Statement
<description>



Running `devsynth run-tests` across speed categories triggers internal pytest-xdist assertion errors, preventing full suite completion.

## Plan

- Investigate pytest-xdist configuration and plugin compatibility.
- Ensure `devsynth run-tests` completes without internal assertion errors across fast, medium, and slow categories.



## Action Plan
- <tasks>

## Progress
- 2025-02-19: fast suite passes without assertions; medium and slow remain unverified.

- Attempted `devsynth run-tests --speed=fast`; after initial output the process hung and required manual interruption, indicating ongoing runner issues.
- Dependency on marker normalization resolved by [Issue 151](archived/Normalize-and-verify-test-markers.md).
- 2025-08-16: `poetry run devsynth run-tests --speed=fast` completed with 36 passed and 19 skipped tests, no xdist assertion errors observed; medium and slow categories remain unverified.
- 2025-08-18: Re-running `poetry run devsynth run-tests --speed=fast` stalled during the CLI import sequence and required manual interruption; medium and slow categories remain unverified.
- 2025-08-18: `poetry run devsynth run-tests --speed=fast` now fails at `test_execute_a_shell_command_through_mvu` due to the missing `mvu exec` subcommand. No pytest-xdist assertion errors observed. `--speed=medium` produced no output before hanging, and `--speed=slow` reported no tests. Coverage resets from `reset_coverage` appear to prevent collector issues.
- 2025-02-14: `poetry run pytest -n auto --dist load` exposed a coverage collector assertion; updated test fixtures to reset coverage state between runs.
- 2025-08-18: Added skip for missing MkDocs Material plugin so `poetry run devsynth run-tests --speed=fast` succeeds with 104 passed and 20 skipped tests. Attempts to run `--speed=medium` and `--speed=slow` launched extensive BDD suites and were aborted without pytest-xdist assertion errors.

## References

- Related: [Expand test generation capabilities](Expand-test-generation-capabilities.md)
