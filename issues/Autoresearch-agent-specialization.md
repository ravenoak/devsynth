Milestone: 0.1.0-alpha.2
Status: open
Owner: WSDE Collaboration Guild

Priority: high
Dependencies: docs/specifications/wsde-agent-model-refinement.md, docs/analysis/autoresearch_evaluation.md

## Problem Statement
The WSDE collaboration model lacks explicit Autoresearch personas, leaving
research planning, source vetting, and synthesis fragmented across existing
roles. Without dedicated responsibilities and telemetry, research initiatives are
hard to audit and optimise.

## Action Plan
- [x] Implement Research Lead, Bibliographer, and Synthesist personas mapped to
      WSDE core roles and controlled by CLI flags.
- [x] Update primus selection heuristics to respect Autoresearch expertise
      signals without regressing default task allocation.
- [x] Emit MVUU trace checkpoints and documentation that clarify research
      hand-offs and expected deliverables.
- [x] Extend prompts and training data with persona expectations and fallback
      behaviours (templates/prompts/autoresearch_personas.json,
      templates/prompts/autoresearch_persona_training.jsonl, and updated
      MVUU telemetry specs/tests).

## Acceptance Criteria
- [x] Behaviour tests demonstrate persona assignment, collaboration checkpoints,
      and knowledge graph integration across the Autoresearch workflow.
- [x] Unit tests cover CLI toggles, telemetry payloads, and primus selection
      adjustments.
- [x] MVUU dashboards surface Autoresearch overlays with trace IDs linked to
      research summaries.
- [x] Documentation highlights research responsibilities and failure modes for
      each persona.

## References
- docs/specifications/wsde-agent-model-refinement.md
- docs/analysis/autoresearch_evaluation.md
- docs/analysis/mvuu_dashboard.md
- tests/behavior/features/wsde_agent_model_refinement.feature
