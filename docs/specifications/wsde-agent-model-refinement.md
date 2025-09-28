---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-10-20
status: review
tags:

- specification
- autoresearch

title: WSDE Agent Model Refinement
version: 0.1.0-alpha.1
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
  WSDE teams provide flexible collaboration but lack specialised research roles
  that can drive Autoresearch tasks without overloading Designer or Evaluator
  personas.
- What proofs confirm the solution?
  Behaviour-driven tests cover role assignment, primus rotation, and research
  persona workflows while MVUU traces demonstrate improved critique quality and
  reduced iteration counts when Autoresearch roles are active.

## Motivation

DevSynth's WSDE organisation already supports dynamic role assignment, dialectical
reasoning, and knowledge graph integration. The Autoresearch RFC introduces new
workstreams—scoping research questions, evaluating sources, and synthesising
findings—that benefit from explicitly trained personas. Formalising these roles
keeps the collaboration model intelligible, preserves accountability, and allows
agents to record research provenance consistently.

## Specification

- Extend the WSDE role taxonomy with three research personas:
  - **Research Lead**: orchestrates research objectives, defines knowledge graph
    queries, and manages Autoresearch task queues.
  - **Bibliographer**: validates sources, tracks citation provenance, and
    maintains links between research artefacts and requirements.
  - **Synthesist**: converts vetted findings into actionable implementation
    guidance, ensuring critiques and solutions incorporate research insights.
- Update the `WSDETeam` role assignment matrix:
  - `assign_roles` maps each persona to an underlying WSDE core role (Lead →
    Supervisor, Bibliographer → Designer, Synthesist → Evaluator) while allowing
    agents to hold both a core and research role.
  - `select_primus_by_expertise` considers research proficiency scores when tasks
    include an `autoresearch` flag.
- Add Autoresearch collaboration checkpoints:
  - After the Expand phase, the Research Lead records the active hypothesis set
    and outstanding research questions in memory.
  - Before Retrospect, the Synthesist publishes a `research_summary` artefact and
    links it to MVUU trace entries.
- Implement CLI flags (`--research-personas` and `--research-metrics`) that toggle
  persona activation and emit MVUU-compatible telemetry.
- Document research role responsibilities and failure modes so training data and
  runtime prompts reinforce expectations.

## Acceptance Criteria

- Behaviour scenarios demonstrate that Autoresearch tasks assign Research Lead,
  Bibliographer, and Synthesist roles without displacing the existing Worker and
  Supervisor duties.
- Primus rotation prioritises agents with Autoresearch expertise when the task
  includes a research flag, while default behaviour remains unchanged for other
  tasks.
- MVUU traces include research checkpoints that reference knowledge graph
  artefacts and agent decisions.
- Unit tests verify that CLI toggles activate persona instrumentation and emit
  the expected telemetry payloads.

## Proofs

- `wsde_agent_model_refinement.feature` scenarios validate persona assignment and
  MVUU trace generation.
- Unit tests cover the updated primus selection heuristics and telemetry writers.
- Integration tests run Autoresearch tasks end-to-end, confirming that knowledge
  graph insights feed into critiques and synthesis outputs.
