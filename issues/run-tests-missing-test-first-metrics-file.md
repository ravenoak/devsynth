Title: DevSynth run-tests missing test_first_metrics file
Date: 2025-09-10 14:16 UTC
Status: open
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
  - [ ] Correct the test path or update invocation to use `tests/unit/general/test_test_first_metrics.py`.
  - [ ] Rerun `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel`.
Resolution Evidence:
  - pending green run artifacts
