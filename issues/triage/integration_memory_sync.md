# Integration: Memory Sync (LMDB/FAISS/Kuzu) — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures and flakiness related to cross-store synchronization.

## Reproduction
poetry run pytest -q tests/integration/memory -k sync

## Thesis / Antithesis / Synthesis
- Thesis: TBD
- Antithesis: TBD
- Synthesis: TBD

## Proposed Fix
- Steps: Align interfaces; finalize sync manager semantics across backends.
- Tests: Expand cross-store sync coverage with deterministic datasets.

## Acceptance Criteria (BDD)
Given the integration memory sync tests
When run under minimal and full extras
Then cross-store sync is deterministic, consistent, and passes across all configured backends.
