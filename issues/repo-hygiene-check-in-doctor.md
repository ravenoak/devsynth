# Integrate repo hygiene check into `devsynth doctor`
Milestone: 0.1.x
Status: Proposed
Priority: Medium
Dependencies: epics/scripts-consolidation-into-main-application.md

## Problem Statement
`scripts/repo_hygiene_check.py` identifies untracked transient artifacts but is not available via the main CLI. Developers expect `devsynth doctor` to surface repository hygiene issues.

## Action Plan
- Add a hygiene sub-check to `doctor_cmd` that:
  - Runs `git status --porcelain`, extracts untracked paths, matches against transient patterns.
  - Prints offenders and remediation guidance.
  - Supports `--strict` (exit non-zero when offenders exist).
- Keep pattern list in one place; document relationship to `.gitignore`.
- Consider a `--hygiene-only` flag for quick checks.

## Acceptance Criteria
- `devsynth doctor` surfaces hygiene findings with clear remediation tips.
- Optional `--strict` toggles exit code behavior when issues are present.
- Patterns documented and deduplicated.

## References
- `scripts/repo_hygiene_check.py`
- `src/devsynth/application/cli/commands/doctor_cmd.py`
