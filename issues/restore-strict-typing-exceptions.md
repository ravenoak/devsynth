# Restore strict typing for devsynth.exceptions
Milestone: 0.1.0-alpha.1
Status: closed

## Problem Statement
`devsynth.exceptions` used `ignore_errors=true` in `pyproject.toml`, bypassing type checks.

## Resolution
- Added type hints for custom exception fields and annotated all constructors with `-> None`.
- Removed the `ignore_errors` override from `pyproject.toml`.
- `poetry run mypy src/devsynth/exceptions.py` reported no issues.
- `poetry run devsynth run-tests --speed=fast` produced no output in this environment.
- Closed on 2025-09-14.

## Action Plan
- [x] Add type hints for all custom exceptions.
- [x] Remove the `ignore_errors` override from `pyproject.toml`.
- [x] Update `issues/typing_relaxations_tracking.md` and close this issue.
