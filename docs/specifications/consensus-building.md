---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-29
status: review
tags:
  - specification
  - wsde
  - consensus

title: Consensus Building
version: 0.1.0-alpha.1
---

# Summary

Consensus building ensures WSDE teams surface expertise-weighted perspectives,
resolve conflicts, and document final decisions with rationale. The executable
stories in
[`tests/behavior/features/general/consensus_building.feature`](../../tests/behavior/features/general/consensus_building.feature)
set the baseline behaviour for voting, conflict mediation, and decision history.
Companion scenarios in
[`tests/behavior/features/general/delegate_task_consensus.feature`](../../tests/behavior/features/general/delegate_task_consensus.feature)
and
[`tests/behavior/features/general/wsde_voting_mechanisms.feature`](../../tests/behavior/features/general/wsde_voting_mechanisms.feature)
extend those flows into delegation and voting tie-breakers.

## Motivation

WSDE collaboration depends on transparent decision paths. Weighted voting and
conflict resolution must align with the domain models in
[`src/devsynth/domain/models/wsde_voting.py`](../../src/devsynth/domain/models/wsde_voting.py)
and
[`src/devsynth/domain/models/wsde_decision_making.py`](../../src/devsynth/domain/models/wsde_decision_making.py).
The team coordinator integrates these models via
[`src/devsynth/application/collaboration/wsde_team_consensus.py`](../../src/devsynth/application/collaboration/wsde_team_consensus.py),
so the specification keeps the documentation synchronized with the behaviour the
unit suites assert.

## Specification

- **Weighted voting**: Each decision captures agent votes along with expertise
  weights. Weighted tallies determine the preferred option, and rationale is
  stored alongside the vote to justify the weighting.
- **Conflict resolution**: When conflicts arise the team records dissenting
  positions, triggers facilitated dialogue, and documents the steps taken to
  address the concerns before recording the consensus result.
- **Tie-breaking**: Predefined strategies (e.g., primus adjudication,
  escalation, or expertise comparison) apply deterministically when weighted
  voting ends in a tie, with the chosen method captured in the decision history.
- **Decision tracking**: Decision records include contributors, weighted scores,
  conflict notes, applied tie-breaking strategy, and a narrative explanation
  suitable for stakeholder review.

## Acceptance Criteria

- Behaviour suites for consensus building, delegation, and voting mechanisms run
  with consistent role statements and scenario names across the general and
  mirrored features, demonstrating parity in how teams record votes, resolve
  conflicts, and document history.
- Consensus services serialize decision outcomes, participant metadata, and
  conflict indicators as validated by unit tests including
  [`tests/unit/application/collaboration/test_wsde_team_consensus_utils.py`](../../tests/unit/application/collaboration/test_wsde_team_consensus_utils.py),
  [`tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py`](../../tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py),
  and
  [`tests/unit/application/collaboration/test_wsde_memory_sync_hooks.py`](../../tests/unit/application/collaboration/test_wsde_memory_sync_hooks.py).
- Decision histories propagate through orchestration layers without data loss,
  satisfying the integration points in
  [`src/devsynth/consensus.py`](../../src/devsynth/consensus.py) and the
  collaboration coordinator tests that verify consensus payloads.

## Traceability

- **Behaviour**: `consensus_building.feature`, `delegate_task_consensus.feature`,
  `wsde_voting_mechanisms.feature`
- **Domain models**: `domain/models/wsde_voting.py`,
  `domain/models/wsde_decision_making.py`,
  `application/collaboration/wsde_team_consensus.py`, `consensus.py`
- **Unit suites**: `tests/unit/application/collaboration/test_wsde_team_consensus_utils.py`,
  `tests/unit/application/collaboration/test_wsde_team_consensus_conflict_detection.py`,
  `tests/unit/application/collaboration/test_wsde_memory_sync_hooks.py`
