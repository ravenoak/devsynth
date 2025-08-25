# Integration Test Suite Triage

Purpose: Inventory integration test failures, categorize by subsystem, and create actionable sub-issues per module. Maintained iteratively per .junie/guidelines.md.

Updated: 2025-08-24
Owner: QA/DevInfra

## How to Reproduce

- Minimal dependencies (CI-fast):
  - poetry install --with dev --extras minimal
  - poetry run pytest -q tests/integration

- Full extras (when needed):
  - poetry install --all-extras --all-groups
  - poetry run pytest -q tests/integration

## Inventory

- [ ] Subsystem: Memory (LMDB/FAISS/Kuzu sync)
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/integration/memory -k sync
  - Linked issue: issues/triage/integration_memory_sync.md
- [ ] Subsystem: Providers (stubs)
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/integration/providers
  - Linked issue: issues/triage/integration_providers.md
- [ ] Subsystem: Orchestration
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/integration/orchestration
  - Linked issue: issues/triage/integration_orchestration.md

## Sub-Issues

- issues/triage/integration_memory_sync.md
- issues/triage/integration_providers.md
- issues/triage/integration_orchestration.md

## Notes

- Ensure provider tests use deterministic local stubs; no live network.
- Respect speed markers; prefer fast subset for PRs.
- Align with docs/roadmap/release_plan.md and tests/fixtures seeding.
