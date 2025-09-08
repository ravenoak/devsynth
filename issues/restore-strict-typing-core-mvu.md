# Restore strict typing for devsynth.core.mvu.*
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
Modules under `devsynth.core.mvu.*` disable `disallow_untyped_defs`, `check_untyped_defs`, and `ignore_missing_imports` in `pyproject.toml`, limiting type coverage.

## Action Plan
- [ ] Add missing type annotations across MVU core modules.
- [ ] Provide or stub missing imports and enable strict mypy checks.
- [ ] Remove the overrides from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.
