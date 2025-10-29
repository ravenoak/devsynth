---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-29
status: review
tags:
  - specification
  - wsde
  - consensus

title: Delegating tasks with consensus voting
version: 0.1.0a1
---

# Summary

Delegating tasks with consensus voting ensures hand-offs respect the team decision
record and carry expertise-weighted outcomes into execution. Executable stories
in
[`tests/behavior/features/general/delegate_task_consensus.feature`](../../tests/behavior/features/general/delegate_task_consensus.feature)
outline how WSDE teams coordinate delegation, handle missing solutions, and
surface dialectical failures. The workflow-specific mirror at
[`tests/behavior/features/delegating_tasks_with_consensus_voting.feature`](../../tests/behavior/features/delegating_tasks_with_consensus_voting.feature)
keeps regression coverage aligned with the general behaviours.

## Motivation

Delegation sits downstream of consensus. Documenting the steps captured in the
general feature ensures the coordinator implementation in
[`src/devsynth/application/collaboration/wsde_team_consensus.py`](../../src/devsynth/application/collaboration/wsde_team_consensus.py)
and
[`src/devsynth/application/collaboration/coordinator.py`](../../src/devsynth/application/collaboration/coordinator.py)
remains aligned with the domain utilities in
[`src/devsynth/domain/models/wsde_voting.py`](../../src/devsynth/domain/models/wsde_voting.py)
and the safeguards validated by unit tests. Explicit traceability prevents drift
between consensus outcomes and execution hand-offs.

## Specification

- **Delegated consensus decision**: `WSDETeamCoordinator.delegate_task` packages
  the consensus-approved option, contributing agents, and the applied method (for
  example, `consensus_vote` or `fallback`).
- **No-solution fallback**: When no agent proposes a solution, the coordinator
  returns a structured payload with explanatory metadata and records the failure
  reason for audit.
- **Dialectical error handling**: Dialectical reasoning failures produce
  user-friendly error responses while maintaining system consistency.
- **Consensus payload propagation**: Delegation results include vote tallies,
  expertise weights, and rationale sourced from the upstream consensus decision.
- **History logging**: Each delegation attempt appends to the decision history so
  downstream automation can reconcile execution outcomes with the consensus log.

## Acceptance Criteria

- Mirrored features reuse the role statements and scenario names from the general
  feature, demonstrating parity for consensus hand-offs, no-solution fallbacks,
  and dialectical error handling.
- Delegation utilities serialize consensus payloads, contributor metadata, and
  fallback reasons as validated by
  [`tests/unit/application/collaboration/test_delegate_workflows.py`](../../tests/unit/application/collaboration/test_delegate_workflows.py)
  and
  [`tests/unit/application/collaboration/test_wsde_team_consensus_utils.py`](../../tests/unit/application/collaboration/test_wsde_team_consensus_utils.py).
- Integration coverage in
  [`tests/integration/general/test_run_pipeline_command.py`](../../tests/integration/general/test_run_pipeline_command.py)
  demonstrates the CLI exposes the same delegation semantics exercised in the
  behaviour suites.

## Traceability

- **Behaviour**: `delegate_task_consensus.feature`,
  `delegating_tasks_with_consensus_voting.feature`
- **Domain models**: `application/collaboration/wsde_team_consensus.py`,
  `application/collaboration/coordinator.py`,
  `domain/models/wsde_voting.py`
- **Unit suites**: `tests/unit/application/collaboration/test_delegate_workflows.py`,
  `tests/unit/application/collaboration/test_wsde_team_consensus_utils.py`
