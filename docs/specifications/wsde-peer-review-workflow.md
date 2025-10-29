---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-29
status: review
tags:
  - specification
  - wsde
  - peer-review

title: WSDE Peer Review Workflow
version: 0.1.0a1
---

# Summary

The WSDE peer review workflow orchestrates structured messaging, reviewer
coordination, and revision tracking so teams can iterate with audit-ready
evidence. The executable baseline in
[`tests/behavior/features/general/wsde_message_passing_peer_review.feature`](../../tests/behavior/features/general/wsde_message_passing_peer_review.feature)
defines the required behaviour for each scenario—message routing, broadcast
delivery, priority handling, structured payloads, reviewer assignment,
acceptance criteria, revision loops, dialectical critique, and history
persistence. The mirrored workflow suite at
[`tests/behavior/features/wsde_peer_review_workflow.feature`](../../tests/behavior/features/wsde_peer_review_workflow.feature)
confirms the workflow-specific wiring matches the general behaviour.

## Motivation

Peer review is a critical WSDE control point. Aligning the specification with
the shared feature file ensures the workflow remains consistent with the domain
models that implement routing and review persistence in
[`src/devsynth/domain/wsde/workflow.py`](../../src/devsynth/domain/wsde/workflow.py)
and
[`src/devsynth/domain/models/wsde_utils.py`](../../src/devsynth/domain/models/wsde_utils.py),
plus the orchestration logic in
[`src/devsynth/application/collaboration/peer_review.py`](../../src/devsynth/application/collaboration/peer_review.py).
Explicitly mapping documentation to the scenarios keeps message schemas,
reviewer lifecycles, and revision tracking aligned with the unit suites and the
auditable records expected by downstream EDRR phases.

## Specification

- **Message passing between agents**: The workflow records sender, recipient,
  type, and timestamps for direct messages so targeted updates travel through
  WSDE queues exactly as shown in the "Message passing between agents"
  scenario.
- **Broadcast message to multiple agents**: Broadcasts store a single event with
  derived recipients, preserving sender/type metadata and ensuring every agent
  receives the assignment, mirroring the broadcast scenario.
- **Message passing with priority levels**: Priority flags drive queue ordering
  so high-priority updates are processed first and annotated in history.
- **Message passing with structured content**: Structured payloads remain
  queryable by key (task id, status, completion, blockers) and are available to
  supervising agents exactly as the structured-content scenario prescribes.
- **Peer review request and execution**: Submissions trigger expertise-aware
  reviewer assignment, distribute individual review tasks, and aggregate feedback
  for the author.
- **Peer review with acceptance criteria**: Review requests carry acceptance
  criteria that reviewers evaluate, producing per-criterion pass/fail signals and
  an overall decision.
- **Peer review with revision cycle**: Reviewer feedback loops until approval;
  each revision is stored with provenance so history reflects every cycle.
- **Peer review with dialectical analysis**: Critic agents capture thesis,
  antithesis, and synthesis insights that accompany the review payload.
- **Message and review history tracking**: Communication and review events stay
  filterable by agent, message type, and time period for audit and monitoring.

## Acceptance Criteria

- The mirrored workflow feature executes the same role statements and scenario
  names as the general feature, demonstrating parity for each behaviour listed
  above.
- Domain and application utilities persist peer review messages, reviewer
  outcomes, consensus fallbacks, and dialectical artefacts as exercised by
  [`tests/unit/domain/test_wsde_peer_review_workflow.py`](../../tests/unit/domain/test_wsde_peer_review_workflow.py),
  [`tests/unit/application/collaboration/test_peer_review_store.py`](../../tests/unit/application/collaboration/test_peer_review_store.py),
  and
  [`tests/unit/general/test_wsde_team_extended.py`](../../tests/unit/general/test_wsde_team_extended.py).
- The workflow exposes retrieval APIs that satisfy history and revision access
  expectations in
  [`src/devsynth/application/collaboration/peer_review.py`](../../src/devsynth/application/collaboration/peer_review.py).

## Traceability

- **Behaviour**: `wsde_message_passing_peer_review.feature`,
  `wsde_peer_review_workflow.feature`
- **Domain models**: `domain/wsde/workflow.py`, `domain/models/wsde_utils.py`,
  `application/collaboration/peer_review.py`
- **Unit suites**: `tests/unit/domain/test_wsde_peer_review_workflow.py`,
  `tests/unit/application/collaboration/test_peer_review_store.py`,
  `tests/unit/general/test_wsde_team_extended.py`
