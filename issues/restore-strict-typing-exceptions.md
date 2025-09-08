# Restore strict typing for devsynth.exceptions
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
`devsynth.exceptions` uses `ignore_errors=true` in `pyproject.toml`, bypassing type checks.

## Action Plan
- [ ] Add type hints for all custom exceptions.
- [ ] Remove the `ignore_errors` override from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.
