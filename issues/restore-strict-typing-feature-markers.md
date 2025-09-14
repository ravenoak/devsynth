# Restore strict typing for devsynth.feature_markers
Milestone: 0.1.0-alpha.1
Status: closed

## Problem Statement
`devsynth.feature_markers` disables `disallow_untyped_defs` and `check_untyped_defs` in `pyproject.toml`, reducing type safety.

## Action Plan
- [x] Add explicit type annotations and enable strict mypy checks.
- [x] Remove the override from `pyproject.toml`.
- [x] Update `issues/typing_relaxations_tracking.md` and close this issue.
