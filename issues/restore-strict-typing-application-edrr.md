# Restore strict typing for devsynth.application.edrr.*
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
Modules under `devsynth.application.edrr.*` use `ignore_errors=true` in `pyproject.toml`, so they are not type-checked.

## Action Plan
- [ ] Annotate EDRR application modules and resolve typing problems.
- [ ] Remove the `ignore_errors` override from `pyproject.toml`.
- [ ] Update `issues/typing_relaxations_tracking.md` and close this issue.

## Progress
- 2025-09-13: Running `poetry run mypy src/devsynth/application/edrr` reported 430 errors across multiple modules, so the
  `ignore_errors` override remains and further annotation work is required.
