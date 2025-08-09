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

## Review Process

1. Run the security checks:
   ```bash
   poetry run pre-commit run --all-files bandit safety
   ```
   or
   ```bash
   poetry run python scripts/dependency_safety_check.py
   ```
2. Record findings in the issue tracker.
3. Prioritize and remediate identified vulnerabilities.
4. Close issues once fixes are merged and verified.

## Responsibilities

The security lead coordinates reviews and ensures remediation tasks are
assigned to the appropriate maintainers.
