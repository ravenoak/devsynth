# Periodic Security Review

Regular security reviews ensure that DevSynth's safeguards remain effective and compliant.

## Review Cadence
- Conduct a review at least once per quarter.
- Trigger an additional review after significant dependency or architecture changes.

## Procedure
1. Run `scripts/security_audit.py` to execute Bandit and Safety scans.
2. Address or document all reported issues.
3. Verify that pre-deploy policy checks pass via `require_pre_deploy_checks`.
4. Record outcomes in the project's security log for traceability.
