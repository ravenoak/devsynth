# WSDE role mapping for release readiness

Status: OPEN
Priority: Medium
Owner: WSDE Coordination – Maya Ortiz
Created: 2025-10-03

## Summary

The WSDE framework defines Designer, Worker, Supervisor, Evaluator, and Primus roles, but release tasks (coverage gate, typing gate, evidence archival) are not yet aligned to those responsibilities. This gap makes it hard to audit multi-agent contributions for 0.1.0a1. The new knowledge graph enablers provide the structure for evidence nodes; this issue captures the human+agent planning work needed to operationalize the roles.【F:docs/architecture/agent_system.md†L324-L340】【F:docs/specifications/knowledge-graph-release-enablers.md†L153-L228】

## Objectives

1. Produce a role-to-task matrix tying each release checklist item (`docs/release/0.1.0-alpha.1.md`) to a WSDE role owner.
2. Document the execution workflow (Designer → Worker → Supervisor → Evaluator → Primus) for coverage runs, typing runs, and knowledge graph ingestion, noting that the Worker now records the `[knowledge-graph]` banner IDs emitted by the CLI and shares them with the Supervisor/Evaluator for validation.
3. Update automation scripts or Taskfile targets with annotations indicating the responsible role for each step.
4. Define audit checkpoints where the Primus validates that gate status, graph evidence, and documentation stay synchronized.

## Acceptance criteria

- [ ] Role mapping matrix committed under `docs/release/` or `docs/specifications/` linking tasks, commands, and evidence references.
- [ ] Release rehearsals log which role executed each gating command, enabling traceability in future retros.
- [ ] Knowledge graph ingestion scripts emit structured logs referencing the acting role (Supervisor/Evaluator).
- [ ] `docs/release/0.1.0-alpha.1.md` reflects gate status updates aligned with Evaluator responsibilities.【F:docs/release/0.1.0-alpha.1.md†L1-L82】

## Dependencies

- `docs/specifications/knowledge-graph-release-enablers.md` (role guidance)
- `issues/knowledge-graph-schema-extension-alpha.md` (schema support)
- `issues/test-artifact-kg-ingestion.md` (instrumentation)
