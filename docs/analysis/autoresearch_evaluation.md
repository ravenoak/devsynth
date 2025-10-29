---
title: "Autoresearch RFC Evaluation"
date: "2025-10-20"
version: "0.1.0a1"
tags:
  - "analysis"
  - "autoresearch"
  - "dialectical"
status: "draft"
author: "DevSynth Strategy Guild"
last_reviewed: "2025-10-20"
---

# Autoresearch RFC Evaluation

The Autoresearch RFC outlines a three-part uplift that depends on DevSynth
linking to the external Autoresearch service instead of embedding research
capabilities locally: enrich the knowledge graph so research assets become
first-class memory, specialize WSDE agents for research workflows, and extend
traceability dashboards so every inquiry, insight, and implementation artifact
stays auditable. This evaluation applies dialectical and Socratic scrutiny to
each recommendation before translating the approved improvements into tracked
follow-ups. All recommendations reaffirm that no Autoresearch client ships in
0.1.0-alpha.1; the work focuses on stubbing interfaces and documenting
dependencies while teams wait for the MCP, A2A, and SPARQL connectors to come
online.

## Recommendation 1 — Expand the Research Knowledge Graph

### Thesis
- Research adapters already persist RDF triples and expose traversal APIs, so
the RFC proposes onboarding research papers, experiments, and citations as
explicit node types with provenance metadata as soon as the external
Autoresearch bridge can push structured artefacts via the planned MCP and
SPARQL interfaces.

### Antithesis
- Persisting richer semantics risks bloating the store and increasing query
latency, especially when agents interleave Autoresearch traversals with routine
project memory lookups.

### Synthesis
- Adopt a tiered ingestion policy: gate large artefacts behind summaries,
capture provenance attributes, and provide bounded traversal helpers that the
CLI and WSDE agents can call once Autoresearch sessions stream content through
the external connectors. Pair these changes with regression tests that reload
the adapter and validate provenance fields alongside the existing traversal
guarantees.

### Socratic Q&A
- **Q:** How do we prevent research artefacts from overwhelming baseline memory
operations?
  **A:** By reusing the existing breadth-first traversal guards and adding
  explicit `research_artifact` depth limits plus eviction policies that keep core
  project memories resident while archiving stale findings.
- **Q:** How do we confirm provenance survives restarts?
  **A:** Behaviour scenarios should store and reload a research triple set, then
  assert that citation URLs, authors, and timestamps persist exactly like other
  graph metadata.

## Recommendation 2 — Specialize WSDE Agents for Research Roles

### Thesis
- The WSDE framework already rotates primus responsibilities and integrates
knowledge graph insight, so the RFC argues for dedicated Research Lead,
Bibliographer, and Synthesist personas that plug into existing role orchestration
while coordinating Autoresearch tasks once the A2A handshake to the external
service becomes available.

### Antithesis
- Injecting new personas may complicate role assignment logic, creating overlap
with existing Designer or Evaluator duties and diluting accountability if the
specializations lack clear acceptance criteria.

### Synthesis
- Extend the WSDE role roster with research-focused capabilities but bind each
persona to measurable outcomes: Research Leads manage query strategies,
Bibliographers vet sources, and Synthesists translate insights into actionable
implementation guidance. Update the role assignment matrix and BDD coverage so
primus rotation still honours expertise and collaboration checkpoints remain
automated, using mocked A2A sessions until the live Autoresearch channel is
provisioned.

### Implementation Roadmap
- **Research Lead** will inherit Primus leadership alongside supervisor
  oversight, coordinating research queues and ensuring critique cycles remain
  accountable to the existing WSDE rotation contract after the A2A handshake is
  deployed.
- **Bibliographer** will pair evaluator analysis with worker execution so
  citation vetting feeds the same review loops already exercised by WSDE
  evaluators and supervisors. Early CLI toggles should be stubbed to capture
  persona intent without contacting the external service.
- **Synthesist** will extend designer planning with evaluator validation,
  closing the loop between ideation and assessment before work reaches
  implementation. Mock integrations must assert that the persona orchestration
  payloads align with the eventual MCP schema.
- Persona toggles in the CLI will surface these configurations for Autoresearch
  sessions while emitting MVUU telemetry that records assignments, transitions,
  and any expertise-based fallbacks once telemetry can be relayed by the
  external service.

### Socratic Q&A
- **Q:** How do research personas coexist with the core WSDE roles?
  **A:** Map each new persona to a supporting responsibility (e.g., Synthesist →
  Evaluator) and require the primus selector to prioritise agents whose research
  expertise matches the task domain, preventing orphaned duties.
- **Q:** How do we validate that specialization actually improves outcomes?
  **A:** Capture MVUU traces showing that research personas shorten iteration
  counts or increase critique quality once Autoresearch telemetry is available,
  and require tests that compare solution quality before and after
  specialization under controlled scenarios using recorded fixtures.

## Recommendation 3 — Enhance Traceability Dashboards for Autoresearch

### Thesis
- The MVUU dashboard already surfaces TraceID-to-artifact mappings; the RFC
proposes layering Autoresearch context so teams can audit how investigations led
from questions to commits, including knowledge graph hops and agent decisions.

### Antithesis
- Aggregating live agent telemetry, research provenance, and implementation
artifacts risks cluttering the dashboard, confusing teams who only need a quick
status check, and introducing privacy concerns for sensitive research data.

### Synthesis
- Add opt-in Autoresearch overlays: timelines linking MVUU entries to research
queries, filters that isolate Autoresearch traces, and export hooks that redact
sensitive fields by default. Instrument the CLI so each Autoresearch session
emits structured trace records once the external bridge can deliver them, then
verify the dashboard can render the new layers without regressing the default
TraceID view. Until the bridge is available, tests should rely on fixture
payloads that mimic the signed telemetry bundle.

### Socratic Q&A
- **Q:** How do we keep the dashboard approachable for non-research workflows?
  **A:** Ship overlays disabled by default, expose toggles in the UI, and retain
the existing TraceID grid so baseline workflows stay unchanged unless teams opt
  into the richer view.
- **Q:** How do we ensure dashboards stay trustworthy when visualising research
  data?
  **A:** Extend MVUU tests to validate checksum fields and trace provenance, and
  require export routines to include digital signatures or hashes that teams can
  verify alongside knowledge graph provenance entries.

## Outcome

All three recommendations survive dialectical stress testing with scoped guard
rails. Implementation proceeds via the follow-up issues referenced in the
Autoresearch workstream, with milestones chained to the MCP → A2A → SPARQL
integration sequence so engineering teams can deliver incremental, testable PRs
without assuming local Autoresearch ingestion.
