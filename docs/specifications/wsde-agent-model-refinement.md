---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-29
status: review
tags:
  - specification
  - wsde
  - collaboration

title: WSDE Agent Model Refinement
version: 0.1.0-alpha.1
---

# Summary

The refined WSDE agent model codifies peer-based collaboration, context-driven
leadership, autonomous contribution, consensus alignment, and dialectical review.
Executable stories in
[`tests/behavior/features/general/wsde_agent_model.feature`](../../tests/behavior/features/general/wsde_agent_model.feature)
articulate these behaviours, with
[`tests/behavior/features/wsde_agent_model_refinement.feature`](../../tests/behavior/features/wsde_agent_model_refinement.feature)
mirroring them for targeted regression coverage.

## Motivation

WSDE teams adapt roles based on expertise and task context. Aligning the
specification with the domain models in
[`src/devsynth/domain/models/wsde_base.py`](../../src/devsynth/domain/models/wsde_base.py),
[`src/devsynth/domain/models/wsde_context_driven_leadership.py`](../../src/devsynth/domain/models/wsde_context_driven_leadership.py),
[`src/devsynth/domain/models/wsde_roles.py`](../../src/devsynth/domain/models/wsde_roles.py),
and
[`src/devsynth/domain/models/wsde_multidisciplinary.py`](../../src/devsynth/domain/models/wsde_multidisciplinary.py)
keeps the documentation synchronized with how the runtime handles primus
selection, role blending, and dialectical critique coordination.

## Specification

- **Peer-based collaboration**: Teams instantiate with agents operating as peers
  without fixed hierarchies. Any agent can initiate work, and authority rotates
  according to situational expertise.
- **Context-driven leadership**: Primus selection responds to task metadata and
  expertise scores, promoting the agent best suited for the active work item and
  reverting leadership when the context changes.
- **Autonomous contribution**: Agents may propose solutions or critiques at any
  phase, with the system aggregating contributions without ordering constraints.
- **Consensus alignment**: When multiple solutions emerge the team invokes the
  consensus pipeline, ensuring the final decision captures inputs from all
  relevant agents.
- **Dialectical review**: Critic roles apply thesis, antithesis, and synthesis
  analysis to proposed solutions, and the resulting synthesis informs the team
  outcome and stored artefacts.

## Acceptance Criteria

- Behaviour suites demonstrate parity between the general and mirrored features
  for each scenario (peer collaboration, context-driven leadership, autonomous
  collaboration, consensus decisions, and dialectical review).
- Domain logic for primus rotation, peer review, and dialectical analysis is
  exercised by unit suites such as
  [`tests/unit/general/test_wsde_team_extended.py`](../../tests/unit/general/test_wsde_team_extended.py),
  [`tests/unit/general/test_wsde_team_coordinator.py`](../../tests/unit/general/test_wsde_team_coordinator.py),
  and
  [`tests/unit/domain/models/test_wsde_base_methods.py`](../../tests/unit/domain/models/test_wsde_base_methods.py).
- Role metadata and multidisciplinary overlays remain consistent with the
  responsibilities outlined in the domain models listed above.

## Traceability

- **Behaviour**: `wsde_agent_model.feature`, `wsde_agent_model_refinement.feature`
- **Domain models**: `domain/models/wsde_base.py`,
  `domain/models/wsde_context_driven_leadership.py`, `domain/models/wsde_roles.py`,
  `domain/models/wsde_multidisciplinary.py`
- **Unit suites**: `tests/unit/general/test_wsde_team_extended.py`,
  `tests/unit/general/test_wsde_team_coordinator.py`,
  `tests/unit/domain/models/test_wsde_base_methods.py`
