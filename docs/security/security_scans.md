# Security Scans: Bandit & Safety

This document explains how DevSynth performs code and dependency security checks using Bandit and Safety, in alignment with the principles in `.junie/the_real_core.md` and the development guidelines in `project guidelines`.

## Overview

- Bandit: Static analysis for common security issues in Python code (runs over `src/`).
- Safety: Vulnerability scanning for Python dependencies using a curated database.
- CI Workflow: `.github/workflows/security_scan.yml` runs both tools on pushes and pull requests, uploads JSON reports as artifacts, and posts a brief summary.

The scans are advisory by default and do not fail CI yet, enabling iterative triage and documentation of justifications. We can enable strict failure once the baseline is clean.

## Running Locally

Prerequisites:
- Python 3.12+
- Poetry

Install and run:

```bash
poetry install --with dev
poetry run pip install bandit safety
poetry run python scripts/security/security_scan.py
```

Use strict mode to fail on findings:

```bash
poetry run python scripts/security/security_scan.py --strict
```

Outputs:
- `bandit.json` – Bandit findings (JSON)
- `safety.json` – Safety findings (JSON)

If you have a Safety API key (recommended for the full database), export it:

```bash
export SAFETY_API_KEY=your_key_here
```

## Triage and Documentation

Follow these steps for each finding:
1. Reproduce the finding locally and assess severity and exploitability.
2. Prefer code or dependency updates that remove the issue completely.
3. If a finding is a false positive or low risk with compensating controls, document a justification below with:
   - Finding ID / Package / Version
   - Location (file/line or dependency)
   - Justification (why it does not apply or is acceptable temporarily)
   - Planned remediation (if any) and target version

### Current Justifications

- Bandit scan on 2025-09-10 reported 160 high, 2 medium, and 8 low severity issues across `src/`. These findings are temporarily accepted and tracked in `issues/bandit-findings.md` for remediation.

## CI Integration Notes

- Workflow file: `.github/workflows/security_scan.yml`
- Artifacts: `security-reports` (contains `bandit.json` and `safety.json`)
- Summary: The job writes a short report to the GitHub Actions run summary.
- Future: Once baseline is clean and documented, we can flip to strict mode (fail on medium/high) and add SARIF uploads.

## Alignment with DevSynth Principles

- SDD/TDD/BDD: Findings should result in clear specifications and tests where appropriate (e.g., regression tests for insecure patterns).
- Clarity & Maintainability: Prefer straightforward mitigations over complex workarounds.
- Safety by Default: Keep scans in default CI jobs and make local execution easy to encourage continuous hygiene.
