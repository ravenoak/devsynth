---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-29
status: review
tags:
  - specification
  - wsde
  - peer-review

title: WSDE Message Passing and Peer Review
version: 0.1.0a1
---

# Summary

WSDE message passing and peer review provide the communication backbone for
collaborative quality control. Executable scenarios in
[`tests/behavior/features/general/wsde_message_passing_peer_review.feature`](../../tests/behavior/features/general/wsde_message_passing_peer_review.feature)
outline broadcast, priority, structured payload, and review cycles that the
platform must support. The mirrored workflow feature at
[`tests/behavior/features/wsde_message_passing_and_peer_review.feature`](../../tests/behavior/features/wsde_message_passing_and_peer_review.feature)
keeps targeted regression checks in sync.

## Motivation

Reliable peer review depends on predictable messaging semantics and persistent
history. The domain implementation across
[`src/devsynth/domain/models/wsde_base.py`](../../src/devsynth/domain/models/wsde_base.py),
[`src/devsynth/domain/models/wsde_utils.py`](../../src/devsynth/domain/models/wsde_utils.py),
and
[`src/devsynth/application/collaboration/peer_review.py`](../../src/devsynth/application/collaboration/peer_review.py)
relies on these guarantees to route requests, evaluate feedback, and store
results. Updating the specification ensures documentation matches the behaviours
covered by the feature files and unit suites.

## Specification

- **Direct and broadcast messaging**: Agents can send directed messages and
  broadcasts with sender, recipient, type, and timestamp fields captured for each
  event. Broadcasts record a single event with derived recipient metadata.
- **Priority handling**: Message queues respect explicit priority markers,
  ensuring high-priority updates are processed ahead of lower priorities.
- **Structured content**: Messages accept structured payloads (e.g., tabular
  data) that remain queryable by key to support dashboards and audit requests.
- **Peer review execution**: Review submissions trigger reviewer assignment,
  criteria-aware evaluation, dialectical analysis, revision cycles, and history
  tracking as detailed in the feature scenarios.
- **History persistence**: Communication and peer review records remain
  filterable by agent, type, and timeframe for reporting and governance.

## Acceptance Criteria

- Behaviour suites demonstrate parity for message passing, broadcast, priority,
  structured content, reviewer assignment, acceptance criteria, revision cycles,
  dialectical analysis, and history tracking between the general and mirrored
  feature files.
- Domain classes append message metadata and peer review outcomes as validated by
  unit suites such as
  [`tests/unit/domain/models/test_wsde_base_methods.py`](../../tests/unit/domain/models/test_wsde_base_methods.py),
  [`tests/unit/application/collaboration/test_peer_review_store.py`](../../tests/unit/application/collaboration/test_peer_review_store.py),
  and
  [`tests/unit/general/test_wsde_team_extended.py`](../../tests/unit/general/test_wsde_team_extended.py).
- Collaboration services expose retrieval APIs consistent with the message and
  peer review history requirements asserted in the domain and application layers.

## Traceability

- **Behaviour**: `wsde_message_passing_peer_review.feature`,
  `wsde_message_passing_and_peer_review.feature`
- **Domain models**: `domain/models/wsde_base.py`, `domain/models/wsde_utils.py`,
  `application/collaboration/peer_review.py`
- **Unit suites**: `tests/unit/domain/models/test_wsde_base_methods.py`,
  `tests/unit/application/collaboration/test_peer_review_store.py`,
  `tests/unit/general/test_wsde_team_extended.py`
