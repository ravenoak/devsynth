# Instrument test artifacts into the knowledge graph

Status: IN REVIEW
Priority: High
Owner: Release Engineering – Priya Desai
Created: 2025-10-03

## Context

Fast+medium rehearsals (e.g., 2025-10-02) now produce refreshed coverage JSON/HTML artifacts and strict mypy inventories, but the evidence remains filesystem-bound. The RFC-aligned plan requires storing these outputs as `ReleaseEvidence`, `TestRun`, and `QualityGate` nodes so WSDE agents can query gate status programmatically.【F:diagnostics/devsynth_run_tests_fast_medium_20251002T233820Z_summary.txt†L1-L6】【F:diagnostics/mypy_strict_inventory_20251003.md†L1-L31】【F:docs/specifications/knowledge-graph-release-enablers.md†L87-L152】

## Objectives

1. Extend `devsynth.testing.run_tests` to publish coverage manifests via the new adapter helpers after successful `--report` runs. ✅ – implemented by writing `test_reports/coverage_manifest_<UTC>.json` and calling the release graph publisher.
2. Extend the strict typing task (`task mypy:strict`) to publish both the log and the inventory manifest to the knowledge graph. ✅ – `python -m devsynth.testing.mypy_strict_runner` captures both artifacts and publishes the typing gate.
3. Add checksum-based deduplication so repeated rehearsals update existing nodes instead of creating duplicates. ✅ – adapters now match on checksum/run checksum and update nodes instead of inserting duplicates.
4. Surface ingestion telemetry in the CLI output so maintainers know when evidence reached the graph. ✅ – both coverage and typing commands print `[knowledge-graph] …` banners with node IDs.

## Acceptance criteria

- [x] Executing `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` writes a manifest (`.json`) alongside coverage artifacts and creates `TestRun`, `ReleaseEvidence`, and `QualityGate` nodes with the correct relationships.
- [x] Running `poetry run task mypy:strict` updates the `typing` `QualityGate` node with the latest status and evidence.
- [x] Duplicate runs reuse existing nodes when the checksum and timestamp match within one minute.
- [x] CLI output lists the knowledge graph IDs created or updated so WSDE agents and humans can cross-reference evidence quickly.

## Dialectical reasoning snapshot

* **Thesis**: Manual documentation links are sufficient for auditors.
* **Antithesis**: Manual links are error-prone and prevent agents from reasoning over release evidence.
* **Synthesis**: Automate ingestion through adapters while preserving human-readable manifests, enabling both agent automation and manual audit trails.【F:docs/developer_guides/memory_integration_guide.md†L110-L134】

## Dependencies

- `issues/knowledge-graph-schema-extension-alpha.md` (schema changes)
- `issues/wsde-release-role-mapping.md` (role accountability)
