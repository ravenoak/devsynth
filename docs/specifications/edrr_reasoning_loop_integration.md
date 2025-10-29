---
author: ChatGPT
date: 2024-07-01
last_reviewed: 2025-07-16
status: implemented
tags:
  - specification
  - methodology
  - edrr
  - reasoning

title: Integrate reasoning loop with EDRR phases
version: 0.1.0a1
---

# Summary

## Socratic Checklist
- What is the problem?
- What proofs confirm the solution?

## Motivation

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/edrr_reasoning_loop_integration.feature`](../../tests/behavior/features/edrr_reasoning_loop_integration.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.

The dialectical reasoning loop currently operates independently of EDRR phase tracking. Without explicit phase integration, reasoning results are not persisted consistently and consensus failures lack dedicated logging.

## Specification
- Expose a `phase` parameter on `reasoning_loop` allowing callers to specify the active EDRR phase.
- When a coordinator with a memory manager is provided, persist each iteration's results with the given phase.
- Delegate consensus failures to the coordinator so they are logged through standard mechanisms.
- Application coordinators must instantiate a methodology `EDRRCoordinator` and pass it, along with the phase, to `reasoning_loop`.

## Acceptance Criteria
- Dialectical reasoning results are stored in the memory manager under the phase that invoked them.
- Consensus failures during reasoning are logged via `log_consensus_failure`.
- Unit tests cover successful persistence and failure handling.
