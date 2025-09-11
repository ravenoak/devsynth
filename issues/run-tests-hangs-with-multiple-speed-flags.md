Title: DevSynth run-tests hangs with multiple --speed options
Date: 2025-09-11 04:05 UTC
Status: open
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`
Exit Code: 130
Artifacts:
  - diagnostics/run-tests-fast-medium.log
  - `.coverage` (not generated)
Suspected Cause: Providing multiple `--speed` flags appears to stall the CLI before invoking pytest.
Next Actions:
  - [ ] Determine why multiple speed options cause the runner to hang.
  - [ ] Run `poetry run devsynth run-tests` separately for `--speed=fast` and `--speed=medium`.
Resolution Evidence:
  -
