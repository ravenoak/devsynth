Milestone: 0.1.0-alpha.2
Status: open
Owner: Knowledge Systems Guild

Priority: high
Dependencies: docs/specifications/advanced-graph-memory-features.md, docs/analysis/autoresearch_evaluation.md

## Problem Statement
Autoresearch workflows need first-class knowledge graph support so research
artefacts, provenance, and relationships persist alongside core project memory.
Without schema updates and traversal guards, research data risks polluting core
workflows or being lost between sessions.

## Action Plan
- [ ] Implement the `research_artifact` schema extensions and provenance fields
      defined in the advanced graph memory specification.
- [ ] Add bounded traversal helpers and eviction policies that protect baseline
      queries while enabling Autoresearch traversals.
- [ ] Extend CLI ingestion to summarise large artefacts before persistence and
      capture evidence hashes for verification.
- [ ] Update documentation and tutorials to explain Autoresearch ingestion best
      practices.

## Acceptance Criteria
- [ ] Behaviour tests cover Autoresearch ingestion, reload cycles, and bounded
      traversal with and without research nodes.
- [ ] Knowledge graph persistence retains citation URLs, authors, timestamps, and
      evidence hashes across restarts.
- [ ] CLI helpers expose summaries and archival pointers for large artefacts.
- [ ] Release notes document the new schema and migration guidance.

## References
- docs/specifications/advanced-graph-memory-features.md
- docs/analysis/autoresearch_evaluation.md
- tests/behavior/features/advanced_graph_memory_features.feature
