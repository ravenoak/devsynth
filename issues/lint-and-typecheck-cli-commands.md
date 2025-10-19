# Add `devsynth lint` and `devsynth typecheck` commands
Milestone: 0.1.x
Status: Proposed
Priority: Medium
Dependencies: epics/scripts-consolidation-into-main-application.md

## Problem Statement
Developers use `scripts/run_style_checks.py` (Black+isort) and `scripts/run_static_analysis.py` (mypy). These should be first-class CLI commands to reduce fragmentation and improve discoverability.

## Action Plan
- Implement `devsynth lint [--fix]` invoking Black and isort like the existing script.
- Implement `devsynth typecheck` invoking mypy with `pyproject.toml` config.
- Add concise summaries and exit codes matching script behavior.
- Deprecate scripts with clear migration guidance.

## Acceptance Criteria
- Commands exist and mirror script behavior including `--fix`.
- Exit codes match expectations for CI.
- Documentation updated; scripts marked deprecated until removal window ends.

## References
- `scripts/run_style_checks.py`, `scripts/run_static_analysis.py`
