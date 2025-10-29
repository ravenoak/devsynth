---
title: DevSynth Memory Guide
date: 2025-09-30
last_reviewed: 2025-09-30
status: review
version: 0.1.0a1
---

# Memory Guide

DevSynth stores working knowledge in multiple adapters (graph, vector, TinyDB).
This guide highlights the enhanced graph memory workflow and explains how the
external Autoresearch service will contribute artefacts once the integration
sequence (MCP → agent-to-agent → SPARQL) lands. As of the 0.1.0-alpha.1 release
the connectors remain under development, so every Autoresearch reference below
describes preview functionality intended for local stubs and mocks only.

## Research Artefacts

Autoresearch artefacts capture external evidence (papers, datasets, transcripts)
and link it to DevSynth requirements. The enhanced graph adapter defines the
`devsynth:ResearchArtifact` class with provenance fields that will be populated
by the Autoresearch bridge once the external service begins streaming
structured payloads into DevSynth. Until then, populate the fields via fixtures
or CLI stubs so tests remain deterministic:

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
core reasoning stays lightweight. Because the SPARQL gateway is not yet live,
seed artefact nodes via fixtures or mocks rather than real Autoresearch
sessions.

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
`graph_memory.ttl`, and keeps the full file in archival storage. During the
integration window, run these helpers behind feature flags so local experiments
remain hermetic and do not imply direct communication with Autoresearch.

## CLI Integration

`devsynth ingest` now includes stubbed options for the upcoming research
artefact bridge. These flags validate inputs and emit preview warnings, but they
do **not** contact the external Autoresearch service yet:

- `--research-artifact PATH` – Generates summaries and evidence hashes once the
  Autoresearch MCP connector is live. Today the flag validates arguments, logs a
  placeholder, and exits early so scripted workflows can adopt the interface in
  advance.
- `--verify-research-hash HASH=PATH` – Will recompute SHA-256 digests for
  Autoresearch-managed artefacts. Until telemetry arrives from the external
  service, the flag delegates to local hashing helpers and warns that no remote
  verification occurred.

Both options rely on the persisted `graph_memory.ttl` file located under
`$DEVSYNTH_GRAPH_MEMORY_PATH` (defaults to `./.devsynth/memory/`). The file is
reloaded automatically when the adapter starts, so artefacts survive CLI runs
and test sessions. When Autoresearch connectivity is unavailable the CLI should
continue operating against local fixtures while emitting clear warnings that the
external bridge is not yet active.

## Workflow Tips

1. Store artefacts alongside their original filenames so the citation URL
   doubles as an archival pointer once Autoresearch begins referencing the
   remote archive.
2. Run `devsynth ingest --verify-research-hash HASH=path` during release prep to
   confirm that previously published hashes remain valid, acknowledging the
   warning that verification is currently local-only.
3. Use `traverse_graph(start_id, depth, include_research=True)` to gather the
   supporting evidence when preparing audit reports or compliance checklists,
   populating research nodes through fixtures until the SPARQL gateway is
   deployed.

## Autoresearch Interface Roadmap

The Autoresearch bridge will come online in three phases:

1. **Model Context Protocol (MCP)** stubs land first so the external service can
   request ingestion helpers through a consistent tool interface.
2. **Agent-to-Agent (A2A)** handshakes follow, enabling WSDE personas to
   orchestrate Autoresearch sessions and authorize artefact writes.
3. **SPARQL Gateway** activates last, unlocking managed read/write access to
   research nodes once capability negotiation and authentication are stable.

Documentation and CLI affordances described above should remain in "preview"
mode until each milestone completes, keeping user expectations aligned with the
external dependency timeline.
