# Restore strict typing for devsynth.feature_markers
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
`devsynth.feature_markers` disables `disallow_untyped_defs` and `check_untyped_defs` in `pyproject.toml`, reducing type safety.

## Action Plan
- [ ] Add explicit type annotations and enable strict mypy checks.
- [ ] Remove the override from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.
