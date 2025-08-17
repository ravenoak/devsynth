# Periodic Security Review

Regular security reviews ensure that DevSynth's safeguards remain effective and compliant. Automated audits run in continuous integration via the policy gate to block deployments when Bandit or Safety report issues.

## Review Cadence
- Conduct a review at least once per quarter.
- Trigger an additional review after significant dependency or architecture changes.

## Procedure
1. Run the security audit script to execute Bandit and Safety scans.
2. Address or document all reported issues.
3. Confirm required environment flags such as `DEVSYNTH_PRE_DEPLOY_APPROVED` are set and the policy verification script passes.
4. Record outcomes in the project's security log for traceability.
