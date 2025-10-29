---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-22
status: review
tags:

- specification

title: Non-Hierarchical Collaboration
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
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/non_hierarchical_collaboration.feature`](../../tests/behavior/features/non_hierarchical_collaboration.feature) and [`tests/behavior/features/general/non_hierarchical_collaboration.feature`](../../tests/behavior/features/general/non_hierarchical_collaboration.feature) execute via [`tests/behavior/steps/test_non_hierarchical_collaboration_steps.py`](../../tests/behavior/steps/test_non_hierarchical_collaboration_steps.py), verifying peer contribution metrics, role rotation, and adaptive leadership reassignment.
- Complementary collaboration checks in [`tests/behavior/features/general/wsde_agent_model.feature`](../../tests/behavior/features/general/wsde_agent_model.feature) and [`tests/behavior/features/general/delegate_task.feature`](../../tests/behavior/features/general/delegate_task.feature) ensure non-hierarchical behavior persists when delegating and reconciling consensus decisions.
- Unit suites including [`tests/unit/application/collaboration/test_collaborative_wsde_team_task_management.py`](../../tests/unit/application/collaboration/test_collaborative_wsde_team_task_management.py), [`tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py`](../../tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py), and [`tests/unit/application/collaboration/test_wsde_team_extended_peer_review.py`](../../tests/unit/application/collaboration/test_wsde_team_extended_peer_review.py) validate rotation, consensus fallbacks, and peer review workflows without privileged agents.
- Integration coverage in [`tests/integration/general/test_end_to_end_workflow.py`](../../tests/integration/general/test_end_to_end_workflow.py) confirms non-hierarchical coordination survives end-to-end pipelines.


## Specification

- Teams default to peer mode (`WSDETeam.collaboration_mode == "non_hierarchical"`) and record contribution metrics for each task via `get_contribution_metrics`.
- Role assignments rotate as new tasks arrive; the primus role is recalculated through expertise scoring rather than static ordering, and history is captured for auditability.
- Task decomposition distributes subtasks to agents with the highest relevant expertise while allowing collaborative adjustments when progress stalls.
- Leadership reassessment triggers when task requirements change, ensuring agents with the most applicable expertise assume coordination responsibilities mid-stream.

## Acceptance Criteria

- Collaboration metrics credit every participating agent with non-zero contribution for multi-expertise tasks.
- Role history demonstrates primus rotation aligned with expertise changes rather than fixed ordering.
- Subtask assignments adapt when expertise requirements shift or when multi-expertise collaboration is required.
- Behavior and unit suites above pass without module-level skips, demonstrating non-hierarchical control in both BDD and unit harnesses.
