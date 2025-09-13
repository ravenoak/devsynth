# Bandit findings in src
Date: 2025-09-13 05:27 UTC
Status: closed
Affected Area: guardrails

Reproduction:
  - poetry run bandit -r src -ll
Exit Code: 0

Artifacts:
  - diagnostics/bandit_2025-09-10.txt
  - diagnostics/bandit_2025-09-10_run2.txt
  - tmp/bandit.log (2025-09-19)
  - diagnostics/bandit_2025-09-13.txt

Suspected Cause:
  - Multiple potential security issues flagged across modules.
  - Latest scan reports 158 low and 0 medium issues (0 high).

Next Actions:
  - [x] Review high-severity findings and apply fixes or justifications
  - [x] Document accepted risks or suppressions as appropriate

Progress:
  - 2025-09-11: Addressed medium findings with timeouts and nosec rationales; bandit reports 158 low and 0 medium issues.
  - 2025-09-13: Verified bandit scan remains at 158 low and 0 medium issues; no new action required.

Resolution Evidence:
  - 2025-09-11 bandit scan clean (`poetry run bandit -r src -ll`)
  - 2025-09-13 bandit scan clean (`poetry run bandit -r src -ll`)
Related Task: [docs/tasks.md item 11.9.2](../docs/tasks.md)
