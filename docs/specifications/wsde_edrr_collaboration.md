
title: "WSDE-EDRR Collaboration Specification"
date: "2025-07-10"
version: "0.1.0a1"
tags:
  - "specification"
  - "wsde"
  - "edrr"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; WSDE-EDRR Collaboration Specification
</div>

# WSDE-EDRR Collaboration Specification

## 1. Overview

This document specifies the collaboration expectations between the Worker Self-Directed Enterprise (WSDE) model and the EDRR
(Expand, Differentiate, Refine, Retrospect) methodology within DevSynth.

It defines phase progression requirements, memory synchronization behavior, and the mapping between peer-review outcomes and
EDRR results.

## 2. Phase Progression

1. Collaboration cycles must traverse phases in the order `EXPAND → DIFFERENTIATE → REFINE → RETROSPECT` unless explicitly
   rewound by the coordinator.
2. Each phase boundary triggers a role reassessment. The current role mapping MUST be accessible to external consumers.
3. Failed phase prerequisites halt progression and return control to the caller with diagnostic information.

## 3. Memory Flush Behavior

1. Memory updates are queued during phase execution and flushed when a phase completes.
2. A utility function **flush_memory_queue** exposes the queued operations and performs the flush. It returns the flushed items
   so callers may re-queue them to roll back the state if necessary.
3. A companion **restore_memory_queue** function accepts the returned items and re-queues them in their original order.
4. Retrospective phases MUST flush any remaining updates before reporting.
5. If flushing fails or no memory manager is configured, the coordinator emits a final
   sync hook with ``None`` so observers are not left waiting for state propagation.

## 4. Peer-Review Result Mapping

1. Peer-review processes yield one of: `approved`, `changes_requested`, or `rejected`.
2. These statuses map to EDRR results as:
   - `approved` → phase outcome is accepted and persisted.
   - `changes_requested` → phase outcome is stored but marked for rework in the next cycle.
   - `rejected` → phase outcome is discarded and the phase repeats.
3. The mapping is stored alongside review metadata to support traceability.

## 5. DeepAgents Subagent Integration

1. Complex tasks within EDRR phases may spawn specialized subagents using DeepAgents' subagent architecture.
2. Subagents operate with context isolation to maintain focus on specific subtasks while keeping the main agent's context clean.
3. Subagent results are integrated back into the main EDRR workflow through the peer-review process.
4. Subagent spawning is triggered automatically when task complexity exceeds configurable thresholds.
5. Subagent coordination follows the WSDE role model, with spawned agents taking on specialized worker roles.

## 6. Subagent Lifecycle Management

1. Subagents are spawned by the Primus role during task decomposition in the EXPAND phase.
2. Each subagent receives a focused context and specific task assignment.
3. Subagent results are collected and integrated during the REFINE phase.
4. Failed subagents trigger fallback to the main agent workflow with appropriate error handling.
5. Successful subagent completion contributes to the overall EDRR cycle progress tracking.

## 7. References

- [DeepAgents Library](https://github.com/langchain-ai/deepagents)
- [DeepAgents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [EDRR Specification](edrr_cycle_specification.md)
- [WSDE Interaction Specification](wsde_interaction_specification.md)

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/wsde_edrr_collaboration.feature`](../../tests/behavior/features/wsde_edrr_collaboration.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
