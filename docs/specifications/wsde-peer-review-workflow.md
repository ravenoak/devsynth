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
version: 0.1.0-alpha.1
---

# Summary

The WSDE peer review workflow coordinates structured message passing, reviewer
assignment, and revision tracking so teams can iterate on work products with
audit-ready evidence. Behaviour scenarios in
[`tests/behavior/features/general/wsde_message_passing_peer_review.feature`](../../tests/behavior/features/general/wsde_message_passing_peer_review.feature)
and its mirrored suite
[`tests/behavior/features/wsde_peer_review_workflow.feature`](../../tests/behavior/features/wsde_peer_review_workflow.feature)
define the communication and review checkpoints that the workflow must support.

## Motivation

Peer review is a critical control point for the WSDE collaboration model. The
workflow needs to channel role-aware communication, ensure reviewers apply
acceptance criteria, and surface dialectical critiques so that downstream EDRR
phases and compliance reporting can rely on consistent records. Aligning the
specification with the executable stories keeps the workflow behaviour in sync
with the domain models in
[`src/devsynth/domain/wsde/workflow.py`](../../src/devsynth/domain/wsde/workflow.py)
and the peer review utilities in
[`src/devsynth/domain/models/wsde_utils.py`](../../src/devsynth/domain/models/wsde_utils.py).

## Specification

- **Structured message routing**: All peer review requests and updates travel
  through WSDE message queues with sender, recipient, type, and priority fields
  captured as described in the "Message passing" scenarios. Message payloads
  support structured content that can be queried by key for audit and tooling
  integrations.
- **Reviewer assignment and execution**: When a work product is submitted the
  workflow invokes reviewer selection based on expertise metadata. Reviewers
  receive targeted requests, deliver independent evaluations, and the author
  receives the full feedback set.
- **Acceptance criteria and revision cycles**: Review messages embed acceptance
  criteria where provided, record pass/fail outcomes, and capture dialectical
  analysis (thesis, antithesis, synthesis). Revisions loop until reviewers
  approve, with the workflow maintaining version and history metadata.
- **History and persistence**: Communication and review events are appended to
  the peer review history, exposing timestamps, participants, and decision
  rationale for retrieval by orchestration services.

## Acceptance Criteria

- Behaviour scenarios covering message routing, broadcast messaging, structured
  payloads, reviewer assignment, acceptance criteria, revision loops, dialectical
  analysis, and history tracking all execute without divergence between the
  general and workflow-specific feature suites.
- Domain utilities persist peer review records, consensus fallbacks, and message
  metadata as validated by unit suites such as
  [`tests/unit/domain/test_wsde_peer_review_workflow.py`](../../tests/unit/domain/test_wsde_peer_review_workflow.py),
  [`tests/unit/application/collaboration/test_peer_review_store.py`](../../tests/unit/application/collaboration/test_peer_review_store.py),
  and
  [`tests/unit/general/test_wsde_team_extended.py`](../../tests/unit/general/test_wsde_team_extended.py).
- The workflow exposes revision history and dialectical critique artefacts for
  downstream consumers, satisfying the persistence expectations asserted in
  [`src/devsynth/application/collaboration/peer_review.py`](../../src/devsynth/application/collaboration/peer_review.py).

## Traceability

- **Behaviour**: `wsde_message_passing_peer_review.feature`,
  `wsde_peer_review_workflow.feature`
- **Domain models**: `domain/wsde/workflow.py`, `domain/models/wsde_utils.py`,
  `application/collaboration/peer_review.py`
- **Unit suites**: `tests/unit/domain/test_wsde_peer_review_workflow.py`,
  `tests/unit/application/collaboration/test_peer_review_store.py`,
  `tests/unit/general/test_wsde_team_extended.py`
