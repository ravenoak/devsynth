# Bandit findings in src
Date: 2025-09-10 16:19 UTC
Status: open
Affected Area: guardrails

Reproduction:
  - poetry run bandit -r src
Exit Code: 1

Artifacts:
  - diagnostics/bandit_2025-09-10.txt
  - diagnostics/bandit_2025-09-10_run2.txt
  - tmp/bandit.log (2025-09-19)

Suspected Cause:
  - Multiple potential security issues flagged across modules.
  - Latest scan reports 158 low and 12 medium issues (0 high).

Next Actions:
  - [ ] Review high-severity findings and apply fixes or justifications
  - [ ] Document accepted risks or suppressions as appropriate

Progress:
  - 2025-09-30: Re-ran bandit scan; 158 low and 12 medium issues persist.

Resolution Evidence:
  - Pending
