Title: DevSynth run-tests hangs with multiple --speed options
Date: 2025-09-11 04:05 UTC
Status: closed
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`
Exit Code: 130
Artifacts:
  - diagnostics/run-tests-fast-medium.log
  - `.coverage` (not generated)
Suspected Cause: Initial environment lacked installed `devsynth` entry point, causing the CLI to exit prematurely.
Next Actions:
  - [x] Determine why multiple speed options cause the runner to hang.
  - [x] Run `poetry run devsynth run-tests` separately for `--speed=fast` and `--speed=medium`.
  - [x] Re-run with both flags after reinstalling: `poetry install --with dev --all-extras`.
Resolution Evidence:
  - test_reports/fast_medium.log
