# Restore strict typing for devsynth.testing.*
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
Modules under `devsynth.testing.*` use `ignore_errors=true` in `pyproject.toml`, so tests are unchecked by mypy.

## Action Plan
- [ ] Add type annotations to testing utilities.
- [ ] Remove the `ignore_errors` override from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.
