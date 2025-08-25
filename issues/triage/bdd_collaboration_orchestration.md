# BDD: Collaboration & Orchestration — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures from collaboration/orchestration features.

## Reproduction
poetry run pytest -q tests/behavior -k orchestration

## Acceptance Criteria (BDD)
Given collaboration and orchestration BDD scenarios
When intermittent failures are simulated via fixtures
Then retries and error handling behavior match the specifications and tests pass.
