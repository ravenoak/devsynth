# Integration: Providers (stubs and safety) — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures related to provider initialization and error handling with local stubs.

## Reproduction
poetry run pytest -q tests/integration/providers

## Proposed Fix
- Ensure default provider selection respects env vars and falls back safely.
- Add missing stubbed behaviors if any; verify no network calls by default.

## Acceptance Criteria (BDD)
Given provider integration tests
When environment keys are missing
Then provider init short-circuits safely and tests pass using local stubs.
