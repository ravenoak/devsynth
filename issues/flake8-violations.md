# Flake8 violations in src and tests
Date: 2025-09-10 16:19 UTC
Status: open
Affected Area: guardrails

Reproduction:
  - poetry run flake8 src tests
Exit Code: 1

Artifacts:
  - diagnostics/flake8_2025-09-10.txt
  - diagnostics/flake8_2025-09-10_run2.txt
  - tmp/flake8.log (2025-09-19)

Suspected Cause:
  - Widespread lint errors and unused imports across codebase.
  - Latest run shows E501/F401/F841 in tests/unit/testing/test_run_tests_module.py and related files.

Next Actions:
  - [ ] Audit and fix flake8 warnings in src
  - [ ] Audit and fix flake8 warnings in tests

Progress:
- 2025-10-01: `poetry run flake8 src/ tests/` still reports E501/F401/F841; issue reopened.

Resolution Evidence:
  - `poetry run flake8 src tests`
