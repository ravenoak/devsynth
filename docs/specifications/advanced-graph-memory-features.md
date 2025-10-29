---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-10-02
status: published
tags:

- specification
- autoresearch

title: Advanced Graph Memory Features
version: 0.1.0a1
---

<!--
Required metadata fields:
- author: document author
- date: creation date
- last_reviewed: last review date
- status: draft | review | published
- tags: search keywords
- title: short descriptive name
- version: specification version
-->

# Summary

## Socratic Checklist
- What is the problem?
  The graph memory system stores items as RDF triples but lacks explicit
  traversal capabilities, documented guarantees that nodes and links persist
  across adapter restarts, and a schema for Autoresearch artefacts that keeps
  the upcoming external connector boundaries visible to downstream teams.
- What proofs confirm the solution?
  Behaviour-driven tests traverse stored relationships, reload the adapter to
  verify persistence, and validate—via mocked connectors—that Autoresearch
  artefacts retain provenance metadata and bounded traversal behaviour without
  implying the external service already ships inside DevSynth.

## Motivation

Agents reason over relationships between memories. Without a bounded traversal
mechanism, durable graph storage, and a structured way to store research
artefacts, agents cannot reliably follow chains of related items or resume
reasoning after a restart. Providing a documented traversal API with persistence
and research provenance guarantees enables richer memory queries while keeping
expectations clear that the Autoresearch service remains external until the MCP
→ A2A → SPARQL bridge is delivered.

## Specification

- Add a `traverse_graph(start_id, max_depth, *, include_research=False)` method
  to `GraphMemoryAdapter`. The method performs a breadth-first search over
  `devsynth:relatedTo` links, returning the set of reachable node IDs up to the
  specified depth. When `include_research` is `False`, traversal skips
  `research_artifact` nodes so core workflows remain lightweight.
- Persist nodes and relationships to `graph_memory.ttl` whenever items or links
  are stored. On initialization the adapter loads the file if it exists,
  ensuring all nodes, `relatedTo` edges, and research provenance survive process
  restarts.
- Extend the schema with the following Autoresearch constructs, scoped for the
  forthcoming external Autoresearch integration:
  - `devsynth:ResearchArtifact` class with properties `title`, `summary`,
    `citationUrl`, `evidenceHash`, and `publishedAt`.
  - `devsynth:supports` relationships that link a research artefact to
    requirements, issues, or commits.
  - `devsynth:derivedFrom` relationships that connect research artefacts to
    upstream knowledge graph nodes (e.g., experiments, datasets).
  - `devsynth:hasRole` relationships binding artefacts to WSDE personas so
    dashboards can surface provenance responsibilities.
- Provide CLI helpers that summarise large artefacts before ingestion once the
  Autoresearch bridge ships. Until then, keep the CLI flags and documentation in
  preview mode so local commands validate argument flow without attempting to
  call the external service. For large PDFs or datasets, store a digest node
  referencing the original file path while keeping the full content in archival
  storage outside the RDF triple store.
- Surface provenance roles and traversal context in CLI and dashboard views so
  operators can trace how Autoresearch artefacts influence EDRR decisions.
- Expose traversal, persistence, and Autoresearch behaviour through
  behaviour-driven tests exercising graph traversal, reload cycles, provenance
  verification, and integration with other memory stores.

### Termination reasoning

The traversal algorithm employs breadth-first search with an explicit depth
limit and a visited set. Each iteration processes only unvisited nodes and
optionally filters Autoresearch artefacts behind the `include_research` flag,
ensuring termination for any finite graph and preventing cycles from causing
infinite loops.

## Acceptance Criteria

- `GraphMemoryAdapter.traverse_graph` returns all nodes reachable within the
  requested depth, excludes the starting node, and honours the
  `include_research` filter.
- Reloading the adapter from a previously persisted graph reproduces all stored
  nodes, `relatedTo` links, and Autoresearch provenance fields without loss.
- Research artefacts include immutable `evidenceHash` values verified by tests
  that compare stored hashes to recomputed digests.
- Behavioural tests cover traversal, persistence, and Autoresearch workflows
  across TinyDB and ChromaDB backends using mocked external connectors only and
  pass under the `fast` marker.

## Proofs

- `advanced_graph_memory_features.feature` scenarios demonstrate traversal from
  an initial node through multiple hops and verify persistence after adapter
  reload.
- Scenario "Traversal gracefully handles unknown starting nodes" ensures the
  breadth-first traversal helper returns an empty set when the start node is
  absent, guarding the optional research overlay against bad inputs.【F:tests/behavior/features/advanced_graph_memory_features.feature†L23-L25】
- Autoresearch feature scenarios add research artefacts through mocked
  connectors representing the external service, reload the adapter, and query
  provenance fields to confirm durability.
- The traversal and persistence logic lives in
  [`GraphMemoryAdapter`](../../src/devsynth/application/memory/adapters/graph_memory_adapter.py),
  which manages RDF serialisation and Autoresearch provenance metadata updates
  consumed by the CLI helpers.
- Unit and integration tests execute without errors for all memory backends.

## Autoresearch Coordination Interfaces

DevSynth will orchestrate external Autoresearch workflows using a layered
interface plan:

1. **Model Context Protocol (MCP)** – introduces tool-calling surfaces the
   Autoresearch service can invoke when streaming artefact metadata into
   DevSynth. MCP support is a prerequisite for exposing Autoresearch ingestion
   hooks in the CLI.
2. **Agent-to-Agent (A2A) channel** – enables WSDE personas to hand off
   investigative tasks to the Autoresearch primus. The channel depends on MCP
   scaffolding so both sides can negotiate capabilities before a session
   begins.
3. **SPARQL gateway** – provides a sanctioned query surface for the external
   service to read/write research nodes. The gateway requires the A2A handshake
   so DevSynth can authorise writes and map provenance back to local memory
   identifiers.

Specifications in this document must ensure adapters and CLI surfaces can be
exercised via mocks until each connector milestone is delivered, keeping local
tests hermetic while signalling the integration order to downstream teams.
