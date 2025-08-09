---
title: "Security Audit Reviews"
status: "draft"
---

# Security Audit Reviews

Periodic reviews ensure DevSynth addresses security findings in a timely
manner and maintains a secure supply chain.

## Review Schedule

- Audit reports are reviewed at least quarterly.
- Additional reviews occur before major releases.

## Periodic Audit Process

1. Execute the bundled audit script:
   ```bash
   poetry run python scripts/security_audit.py
   ```
   This runs Bandit static analysis and Safety dependency checks.
2. Capture the output and store it with the audit logs.
3. Record findings in the issue tracker.
4. Prioritize and remediate identified vulnerabilities.
5. Close issues once fixes are merged and verified and document completion in the next audit.

## Responsibilities

The security lead coordinates reviews and ensures remediation tasks are
assigned to the appropriate maintainers.
