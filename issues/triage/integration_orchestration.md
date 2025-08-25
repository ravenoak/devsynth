# Integration: Orchestration — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures in orchestration flows and collaboration paths.

## Reproduction
poetry run pytest -q tests/integration/orchestration

## Acceptance Criteria (BDD)
Given orchestration integration tests
When retried under intermittent failure conditions (simulated)
Then the system applies retries and error handling hooks consistently and passes.
