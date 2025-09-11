Title: DevSynth run-tests missing test_first_metrics file
Date: 2025-09-10 14:16 UTC
Status: closed
Affected Area: tests
Reproduction:
  - `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`
  - `poetry run pytest unit/general/test_test_first_metrics.py`
Exit Code: 4
Artifacts:
  - test_reports/20250910_141451/all-tests/report.html (not generated)
  - htmlcov/ (empty)
Suspected Cause: Test invocation references `unit/general/test_test_first_metrics.py` which does not exist; expected `tests/unit/general/test_test_first_metrics.py`.
Next Actions:
  - [x] Correct the test path or update invocation to use `tests/unit/general/test_test_first_metrics.py`.
  - [x] Rerun `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`.
Resolution Evidence:
  - [test_reports/test_first_metrics.log](../test_reports/test_first_metrics.log)
Related Task: [docs/tasks.md item 11.8](../docs/tasks.md)
