# Knowledge graph schema extension for release evidence

Status: OPEN
Priority: High
Owner: Memory Systems – Chen Wu
Created: 2025-10-03

## Problem statement

Release rehearsals now emit structured coverage and typing artifacts, but the NetworkX and Kuzu adapters lack typed nodes to represent this evidence. Without schema updates, WSDE agents cannot audit release readiness through knowledge graph queries, and multi-agent planning remains opaque.【F:docs/specifications/knowledge-graph-release-enablers.md†L1-L86】

## Goals

1. Implement the `ReleaseEvidence`, `TestRun`, and `QualityGate` node types and relationships described in `docs/specifications/knowledge-graph-release-enablers.md`.
2. Provide helper methods in the adapters so instrumentation hooks can create nodes without duplicating graph logic.
3. Validate the new schema using both the in-memory NetworkX adapter and the persistent Kuzu store.

## Non-goals

* Backfilling historical artifacts (tracked separately).
* Implementing instrumentation hooks (see `issues/test-artifact-kg-ingestion.md`).

## Success criteria

- [ ] NetworkX adapter exposes `create_release_evidence`, `create_test_run`, and `record_quality_gate` helpers that accept dataclass inputs and return node IDs.
- [ ] Kuzu adapter mirrors the same API and persists nodes with the required properties (`artifact_type`, `coverage_percent`, thresholds, etc.).
- [ ] Executing the rehearsal ingestion script completes without errors after the schema change.
- [ ] Querying the adapters for `QualityGate` nodes returns both baseline data and linked release evidence.

## Dialectical review

* **Thesis**: Existing adapters already store relationships; we can map evidence onto generic nodes.
* **Antithesis**: Generic nodes obscure release readiness and make auditing brittle.
* **Synthesis**: Introduce typed nodes and helper APIs so evidence remains explicit and machine-auditable while reusing the current adapters.【F:docs/developer_guides/memory_integration_guide.md†L110-L134】

## References

- `docs/specifications/knowledge-graph-release-enablers.md`
- `issues/test-artifact-kg-ingestion.md`
