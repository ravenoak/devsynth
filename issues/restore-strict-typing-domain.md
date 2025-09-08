# Restore strict typing for devsynth.domain.*
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
Modules under `devsynth.domain.*` use `ignore_errors=true` in `pyproject.toml`, leaving domain logic unchecked.

## Action Plan
- [ ] Add type annotations across domain modules.
- [ ] Remove the `ignore_errors` override from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.
