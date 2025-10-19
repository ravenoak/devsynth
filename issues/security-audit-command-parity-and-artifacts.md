# Align `security-audit` with script behavior and artifacts
Milestone: 0.1.x
Status: Proposed
Priority: High
Dependencies: epics/scripts-consolidation-into-main-application.md

## Problem Statement
`scripts/security/security_scan.py` produces `bandit.json` and `safety.json` and supports a `--strict` mode. The `security-audit` CLI should provide the same outputs and semantics so users can rely on one command.

## Action Plan
- Update `security_audit_cmd` to:
  - Persist `bandit.json` and `safety.json` in repo root (or `diagnostics/` if preferred).
  - Support a `--strict` flag that exits non-zero on any detected issues.
  - Print a concise summary with paths to artifacts.
- Ensure Safety key handling (`SAFETY_API_KEY`) mirrors the script.
- Add tests mocking subprocess and file interactions.
- Deprecate `scripts/security/security_scan.py` once parity is achieved.

## Acceptance Criteria
- `devsynth security-audit --strict` produces JSON artifacts and non-zero exit code when issues exist.
- Summary output matches documented expectations.
- Tests validate strict mode, artifact writing, and key handling.

## References
- `src/devsynth/application/cli/commands/security_audit_cmd.py`
- `scripts/security/security_scan.py`
