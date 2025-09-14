Title: DevSynth run-tests missing test_first_metrics file
Date: 2025-09-14 21:35 UTC
Status: open
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` (hangs; logs empty)
  - `poetry run pytest unit/general/test_test_first_metrics.py`
Exit Code: 4
Artifacts:
  - /tmp/full_run.log (empty)
Suspected Cause: Test invocation references `unit/general/test_test_first_metrics.py` which does not exist; expected `tests/unit/general/test_test_first_metrics.py`.
Next Actions:
  - [ ] Remove stale `unit/general/test_test_first_metrics.py` reference and ensure test resides under `tests/unit/general/`.
  - [ ] Rerun `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` after fix and capture coverage artifacts.
Resolution Evidence:
  - [test_reports/test_first_metrics.log](../test_reports/test_first_metrics.log) (previous attempt)
Related Task: [docs/tasks.md item 11.8](../docs/tasks.md)
