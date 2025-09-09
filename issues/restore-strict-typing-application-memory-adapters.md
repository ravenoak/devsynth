# Restore strict typing for devsynth.application.memory.adapters.*
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
Modules under `devsynth.application.memory.adapters.*` use `ignore_errors=true` in `pyproject.toml`, disabling type checks.

## Action Plan
- [ ] Add type annotations for memory adapters.
- [ ] Remove the `ignore_errors` override from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.
