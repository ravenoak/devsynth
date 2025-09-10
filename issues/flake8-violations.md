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

Suspected Cause:
  - Widespread lint errors and unused imports across codebase.
- Latest run shows E501 and F401 in tests/unit/testing/test_run_tests_module.py.

Next Actions:
  - [ ] Audit and fix flake8 warnings in src
  - [ ] Audit and fix flake8 warnings in tests

Resolution Evidence:
  - Pending
