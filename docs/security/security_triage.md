---
author: DevSynth Team
date: "2025-08-26"
status: stable
version: "0.1.0a1"
---
# Security Scan Triage Workflow

This document defines the standard process for running security scans (Bandit and Safety), interpreting results, and handling suppressions with documented rationale. It aligns with project guidelines (Security tools) and the Stabilization Plan (docs/plan.md).

## Tools
- Bandit: static analysis for Python security issues.
  - Recommended command: `poetry run bandit -r src/devsynth -x tests -f json -o security_reports/bandit_report.json`
- Safety: dependency vulnerability scanner.
  - Recommended command: `poetry run safety check --full-report --output json --output-file security_reports/safety_report.json`

CI already runs these tools (see Task 56). This guide is for local triage and documenting decisions.

## Triage Steps
1. Run scans locally (optional) to reproduce CI findings.
2. Classify findings:
   - False positive
   - True positive (needs a fix)
   - Acceptable risk (temporary suppression with timeline)
3. Decide action:
   - Fix immediately if low effort and clear.
   - Suppress only when justified. Every suppression MUST include:
     - Rationale (why acceptable, constraints, plan to remove)
     - Link to an issue/ticket
     - Scope-limited ignore (specific file/check), never global where possible
4. Record outcome:
   - Add an entry to this doc’s “Suppressions Log” (below) with details.
   - Reference the policy files if adding ignores.

## Policy Files
- Bandit policy: `.bandit.yaml`
  - Keep `skips` empty by default. Prefer per-file `# nosec` with a comment explaining the reason and issue link.
- Safety policy: `.safety-policy.toml`
  - Keep `ignore = []` empty by default. If ignoring a vulnerability, include an explicit entry with justification, expiry date, and issue link.

These policy files are present as baselines with zero suppressions to encourage disciplined triage.

## Suppressions Log
- None as of 2025-08-26. All findings should be addressed directly unless documented here with full rationale.

## References
- project guidelines (Security tooling commands)
- docs/plan.md (Stabilization priorities)
- docs/policies/security.md (broader security posture)
- .github/workflows (CI jobs that run bandit/safety)
