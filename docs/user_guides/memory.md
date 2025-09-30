---
title: DevSynth Memory Guide
date: 2025-09-30
last_reviewed: 2025-09-30
status: review
version: 0.1.0-alpha.1
---

# Memory Guide

DevSynth stores working knowledge in multiple adapters (graph, vector, TinyDB).
This guide highlights the enhanced graph memory workflow, including
Autoresearch artefacts introduced in 0.1.0-alpha.1.

## Research Artefacts

Autoresearch artefacts capture external evidence (papers, datasets, transcripts)
and link it to DevSynth requirements. The enhanced graph adapter defines the
`devsynth:ResearchArtifact` class with provenance fields:

- **Title** – human-readable label for the source.
- **Summary** – automatically generated synopsis stored inside the RDF graph.
- **Citation URL** – pointer back to the canonical source or local archive.
- **Evidence Hash** – SHA-256 digest of the archived file, enabling tamper
  detection and reproducibility.
- **Published At** – timestamp (UTC) taken from the artefact's filesystem
  metadata when available.

Artefacts link to other graph nodes via two predicates:

- `devsynth:supports` connects the artefact to requirements, issues, or memory
  items that the evidence substantiates.
- `devsynth:derivedFrom` tracks upstream experiments or datasets that produced
  the artefact.

Graph traversal honours these nodes by default when the caller explicitly opts
in. Use `EnhancedGraphMemoryAdapter.traverse_graph(start_id, depth,
include_research=True)` to include research artefacts in the breadth-first walk;
when `include_research` is `False` (the default) the traversal skips artefacts so
core reasoning stays lightweight.

## Archival Summaries

Large PDFs or datasets should remain outside the RDF triple store. The
`EnhancedGraphMemoryAdapter` exposes helper methods to generate archival
summaries and digests:

```python
adapter = EnhancedGraphMemoryAdapter(base_path=".devsynth/memory", use_rdflib_store=True)
summary = adapter.summarize_artifact(path)
evidence_hash = adapter.compute_evidence_hash(path)
artifact = adapter.ingest_research_artifact_from_path(
    path,
    title=path.stem,
    citation_url=str(path),
    published_at=datetime.datetime.now(datetime.timezone.utc),
    supports=["requirement-123"],
)
```

The helper reads the source file once, stores a compact summary and the hash in
`graph_memory.ttl`, and keeps the full file in archival storage.

## CLI Integration

`devsynth ingest` now ships with two options for research artefacts:

- `--research-artifact PATH` – Generate a summary and evidence hash for the
  artefact at `PATH`, persist the provenance node, and log the resulting digest.
  Repeat the flag to ingest multiple artefacts before the standard ingestion
  flow runs.
- `--verify-research-hash HASH=PATH` – Recompute the SHA-256 digest for `PATH`
  and ensure it matches `HASH`. The command raises a `BadParameter` error if the
  hash differs, preventing stale or tampered evidence from entering the release
  pipeline.

Both options rely on the persisted `graph_memory.ttl` file located under
`$DEVSYNTH_GRAPH_MEMORY_PATH` (defaults to `./.devsynth/memory/`). The file is
reloaded automatically when the adapter starts, so artefacts survive CLI runs
and test sessions.

## Workflow Tips

1. Store artefacts alongside their original filenames so the citation URL
   doubles as an archival pointer.
2. Run `devsynth ingest --verify-research-hash HASH=path` during release prep to
   confirm that previously published hashes remain valid.
3. Use `traverse_graph(start_id, depth, include_research=True)` to gather the
   supporting evidence when preparing audit reports or compliance checklists.
