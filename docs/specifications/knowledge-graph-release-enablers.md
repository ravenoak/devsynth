# Knowledge Graph Release Enablers for 0.1.0a1

Status: draft
Last Updated: 2025-10-03

## Overview

This specification translates the RFC guidance on knowledge graph alignment into near-term deliverables for the 0.1.0a1 release rehearsal. DevSynth already ships NetworkX- and Kuzu-backed adapters that store relationships among project artifacts, but those stores do not yet treat release evidence as first-class nodes.【F:docs/developer_guides/memory_integration_guide.md†L110-L134】 We introduce schema extensions, instrumentation hooks, and WSDE role mappings so multi-agent workflows can reason over coverage and typing gates directly in the knowledge graph.

## Current baseline

* The WSDE knowledge graph utilities expose generic query helpers (`query_knowledge_graph`, `query_related_concepts`, `query_by_concept_type`) that agents can call today, but they lack typed entities for quality evidence and gate status.【F:docs/technical_reference/knowledge_graph_utilities.md†L20-L136】
* WSDE collaborative roles—Designer, Worker, Supervisor, Evaluator, Primus—are documented conceptually, yet they are not anchored to release readiness tasks or knowledge graph responsibilities.【F:docs/architecture/agent_system.md†L324-L340】
* Coverage and typing artifacts (e.g., `coverage.json`, HTML reports, strict mypy inventories) live on disk under `artifacts/` and `diagnostics/` with manual cross-references in documentation, making it difficult for agents to query gate status automatically.【F:diagnostics/devsynth_run_tests_fast_medium_20251002T233820Z_summary.txt†L1-L6】【F:diagnostics/mypy_strict_inventory_20251003.md†L1-L31】

## Enabler A: Schema extensions in the knowledge graph store

**Objective**: add typed entities and relationships that capture release evidence within the existing graph adapters (NetworkX in-memory rehearsal and Kuzu for persistent storage).

**Additions**

* `ReleaseEvidence` node type with properties: `id` (UUID), `release_tag`, `artifact_path`, `artifact_type` (`coverage_json`, `coverage_html`, `mypy_inventory`, `mypy_log`), `collected_at` (UTC ISO-8601), `checksum` (SHA-256), `source_command`.
* `TestRun` node type with properties: `id`, `profile` (`fast`, `medium`, `fast+medium`), `coverage_percent`, `tests_collected`, `exit_code`, `started_at`, `completed_at`.
* `QualityGate` node type with properties: `id`, `gate_name` (`coverage`, `typing`), `threshold`, `status` (`pass`, `fail`, `blocked`), `evaluated_at`.
* Relationships:
  * `(:TestRun)-[:EMITS]->(:ReleaseEvidence)` for coverage JSON/HTML outputs.
  * `(:QualityGate)-[:EVALUATED_FROM]->(:TestRun)` linking gate decisions to specific runs.
  * `(:QualityGate)-[:HAS_EVIDENCE]->(:ReleaseEvidence)` for persistent evidence references.

**Acceptance criteria**

1. Updating the schema in both the NetworkX and Kuzu adapters does not break existing ingestion of documentation or requirements nodes (validated by executing the current rehearsal ingestion script).
2. Creating a `ReleaseEvidence` node and linking it to `TestRun` and `QualityGate` instances succeeds in both adapters without additional configuration.
3. The adapters expose helper methods `create_release_evidence(...)`, `create_test_run(...)`, and `record_quality_gate(...)` that wrap these operations for WSDE agents.
4. Downstream utilities can query `MATCH (g:QualityGate {gate_name: "coverage"})-[:HAS_EVIDENCE]->(e:ReleaseEvidence)` (or the NetworkX equivalent) and retrieve the latest artifacts.

## Enabler B: Instrumentation hooks for test artifacts

**Objective**: automatically project coverage and typing artifacts from release rehearsals into the knowledge graph using the schema extensions above.

**Deliverables**

1. CLI hook in `devsynth.testing.run_tests` that, when `--report` is supplied, writes a manifest alongside `coverage.json` containing checksums, timestamps, and command metadata, then calls `create_test_run`/`create_release_evidence` with the fast+medium summary (e.g., 92.40 % coverage with QualityGate/TestRun/ReleaseEvidence identifiers on 2025-10-12).【F:test_reports/coverage_manifest_20251012T164512Z.json†L1-L56】
2. Typing task wrapper (`task mypy:strict`) publishes the strict inventory (`diagnostics/mypy_strict_inventory_20251003.md`) and the raw mypy log as `ReleaseEvidence` nodes linked to the `typing` quality gate.【F:diagnostics/mypy_strict_inventory_20251003.md†L1-L31】
3. Automation guard that deduplicates artifacts by checksum, ensuring repeated rehearsals update `TestRun` nodes while keeping historical evidence accessible.
4. Backfill script (deferred; see backlog) that ingests previous rehearsal artifacts when available.

**Acceptance criteria**

* Fast+medium rehearsal executed via `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` results in a new `TestRun` node with linked coverage evidence and an updated `coverage` `QualityGate` status.
* Running `poetry run task mypy:strict` with zero or more errors creates or updates the `typing` `QualityGate` node with appropriate status and evidence references.
* WSDE agents can query `QualityGate` nodes to determine whether the release is ready without parsing filesystem artifacts manually.

Implementation tracking: `issues/test-artifact-kg-ingestion.md`.

## Enabler C: WSDE role definitions for release operations

**Objective**: align WSDE collaborative roles with concrete responsibilities for coverage, typing, and evidence archival so multi-agent plans remain auditable.

**Role mapping**

* **Designer** – curates and updates specifications (`docs/specifications/`), including this document and release checklists; ensures schema changes and instrumentation hooks are documented before implementation.
* **Worker** – executes rehearsals (coverage, typing) and triggers instrumentation hooks; owns artifact integrity checksums.
* **Supervisor** – validates that evidence nodes exist in the knowledge graph and that gate statuses match CLI output; raises remediation issues when discrepancies appear.
* **Evaluator** – monitors `QualityGate` nodes, compares thresholds (≥90 % coverage, 0 mypy errors), and flags readiness changes in `docs/release/0.1.0-alpha.1.md`.
* **Primus** – orchestrates cross-role handoffs, coordinates deferred backlog items, and ensures issue traceability for future RFC milestones.

**Acceptance criteria**

1. Each role has at least one associated checklist item in `issues/wsde-release-role-mapping.md`, referencing the relevant instrumentation or schema tasks.
2. Release rehearsal retros capture which role executed each responsibility, keeping multi-agent collaboration auditable.
3. Updates to `docs/release/0.1.0-alpha.1.md` explicitly cite gate status changes and knowledge graph evidence, aligning with the Evaluator responsibilities.

## Deferred backlog

The following items remain out of scope for the 0.1.0a1 rehearsal but are tracked for future RFC iterations:

* Schema normalization and migration tooling for existing graph data sets (`issues/knowledge-graph-schema-extension-alpha.md`).
* Historical artifact backfill script to ingest prior release evidence (same issue as above).
* Automated human sign-off workflow that records reviewer approvals inside the knowledge graph (future issue).

## References

* `issues/test-artifact-kg-ingestion.md`
* `issues/wsde-release-role-mapping.md`
* `issues/knowledge-graph-schema-extension-alpha.md`
