# Restore strict typing for devsynth.domain.*
Milestone: 0.1.0-alpha.1
Status: open

## Problem Statement
Modules under `devsynth.domain.*` use `ignore_errors=true` in `pyproject.toml`, leaving domain logic unchecked.

## Action Plan
- [ ] Add type annotations across domain modules.
- [x] Remove the `ignore_errors` override from `pyproject.toml`.
- [x] Update `issues/typing_relaxations_tracking.md`.

## Progress
- 2025-09-14: Removed `ignore_errors` override for `devsynth.domain.models.requirement` and updated tracking, but `poetry run mypy src/devsynth/domain` reports 617 errors; issue remains open.
