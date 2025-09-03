# Guardrails Non-Green — Formatting/Lint/Typing Failures
Date: 2025-09-02 15:22 local
Status: open
Affected Area: guardrails

Reproduction:
  - poetry run python scripts/run_guardrails_suite.py --continue-on-error
Exit Code: 1

Artifacts:
  - diagnostics/black_check.txt
  - diagnostics/isort_check.txt
  - diagnostics/flake8.txt
  - diagnostics/mypy.txt
  - diagnostics/bandit.txt
  - diagnostics/safety.txt

Suspected Cause:
  - Black/isort drift on several scripts and tests.
  - mypy strict errors across multiple modules not in current iteration scope.

Next Actions:
  - [ ] Fix import order and formatting for a narrow set of newly added/modified files to reduce noise.
  - [ ] Triage mypy errors and decide which modules need relaxations or targeted fixes for 0.1.0a1.
  - [ ] Re-run guardrails and attach updated artifacts; close when green.

Resolution Evidence:
  - Pending
