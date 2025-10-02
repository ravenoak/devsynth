Milestone: 0.1.0-alpha.2
Status: closed
Owner: Knowledge Systems Guild

Priority: high
Dependencies: docs/specifications/advanced-graph-memory-features.md, docs/analysis/autoresearch_evaluation.md

## Problem Statement
Autoresearch workflows need first-class knowledge graph support so research
artefacts, provenance, and relationships persist alongside core project memory.
Without schema updates and traversal guards, research data risks polluting core
workflows or being lost between sessions.

## Action Plan
- [x] Implement the `research_artifact` schema extensions and provenance fields
      defined in the advanced graph memory specification.
- [x] Add bounded traversal helpers and eviction policies that protect baseline
      queries while enabling Autoresearch traversals.
- [x] Extend CLI ingestion to summarise large artefacts before persistence and
      capture evidence hashes for verification.
- [x] Update documentation and tutorials to explain Autoresearch ingestion best
      practices.

## Acceptance Criteria
- [x] Behaviour tests cover Autoresearch ingestion, reload cycles, and bounded
      traversal with and without research nodes.
- [x] Knowledge graph persistence retains citation URLs, authors, timestamps, and
      evidence hashes across restarts.
- [x] CLI helpers expose summaries and archival pointers for large artefacts.
- [x] Release notes document the new schema and migration guidance.

## References
- docs/specifications/advanced-graph-memory-features.md
- docs/analysis/autoresearch_evaluation.md
- tests/behavior/features/advanced_graph_memory_features.feature
- docs/ontology/devsynth.ttl
- diagnostics/autoresearch_graph_queries.md

## Evidence (2025-10-02)
- Added SPARQL-ready ontology (`docs/ontology/devsynth.ttl`) with `hasRole`
  support, matching the dashboard provenance snapshot.
- Implemented WSDE specialist rotation feature tests
  (`tests/behavior/features/wsde_multi_agent.feature`) covering traversal API
  usage.
- CLI ingestion now records provenance roles; see `devsynth ingest` command logs
  and MVUU dashboard "Knowledge Graph Provenance Snapshot" section for runtime
  confirmation.
