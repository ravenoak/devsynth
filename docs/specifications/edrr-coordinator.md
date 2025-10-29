---
author: DevSynth Team
date: 2025-08-19
last_reviewed: 2025-09-22
status: review
tags:

- specification

title: EDRR Coordinator
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
* What is the problem?
* What proofs confirm the solution?

## Problem Statement

Independent agents executing the Expand–Differentiate–Refine–Retrospect (EDRR) cycle can stall or diverge without a
central authority.  In the absence of coordination the phases may execute out of order, recursive micro‑cycles may nest
unboundedly, and the resulting context can become inconsistent across agents.

## Proposed Solution

Introduce an **EDRR Coordinator** that models the cycle as a deterministic finite‑state machine.  The coordinator
sequences the phases in the order `Expand → Differentiate → Refine → Retrospect`, maintains a shared context, and
spawns bounded micro‑cycles to reconcile conflicts.  Each transition updates the context and advances the state until a
terminal `completed` state is reached.

## Motivation

## What proofs confirm the solution?
- Behavior-driven scenarios in [`tests/behavior/features/edrr_coordinator.feature`](../../tests/behavior/features/edrr_coordinator.feature) and [`tests/behavior/features/general/edrr_coordinator.feature`](../../tests/behavior/features/general/edrr_coordinator.feature) exercise initialization, phase progression, manifest-driven execution, and report generation using the shared step implementations in [`tests/behavior/steps/test_edrr_coordinator_steps.py`](../../tests/behavior/steps/test_edrr_coordinator_steps.py) and [`tests/behavior/steps/test_simple_coordinator_steps.py`](../../tests/behavior/steps/test_simple_coordinator_steps.py).
- Recursive micro-cycle governance and template orchestration are verified by unit suites such as [`tests/unit/application/edrr/test_coordinator.py`](../../tests/unit/application/edrr/test_coordinator.py), [`tests/unit/application/edrr/test_micro_cycle_execution.py`](../../tests/unit/application/edrr/test_micro_cycle_execution.py), [`tests/unit/application/edrr/test_phase_management_module.py`](../../tests/unit/application/edrr/test_phase_management_module.py), and [`tests/unit/application/edrr/test_threshold_helpers.py`](../../tests/unit/application/edrr/test_threshold_helpers.py).
- Integration coverage in [`tests/integration/general/test_end_to_end_workflow.py`](../../tests/integration/general/test_end_to_end_workflow.py) and [`tests/integration/general/test_refactor_workflow.py`](../../tests/integration/general/test_refactor_workflow.py) confirms the coordinator's interactions with WSDE teams, memory adapters, and manifest parsing under realistic workflows.
- Termination guarantees and helper bounds are documented in [`docs/implementation/edrr_invariants.md`](../implementation/edrr_invariants.md) and exercised through [`tests/property/test_reasoning_loop_properties.py`](../../tests/property/test_reasoning_loop_properties.py).


The EDRR methodology relies on strict sequencing of phases to ensure that exploration results are
analyzed, refined, and reflected upon in a coherent manner.  Without a coordinator the cycle is
prone to race conditions between agents and to runaway recursion when phases attempt to resolve
conflicts independently.

## Specification

### State Machine

Let the set of states be \(S = \{\text{expand}, \text{differentiate}, \text{refine}, \text{retrospect}, \text{completed}\}\).
The transition function \(\delta\) enforces the strict ordering
`expand → differentiate → refine → retrospect → completed`.  Any attempt to transition out of
order is rejected.

### Context Management

The coordinator maintains a context \(C\).  Each phase produces an output \(o_i\) that is merged
into \(C\) via a deterministic merge operator \(\mu(C, o_i)\).  \(\mu\) is associative and
idempotent, ensuring that repeated application of the same result does not change \(C\).

### Termination Criteria

Recursion depth is bounded by a configured maximum \(d_{\max}\).  A variant function \(\phi =
4\,(d_{\max} - d) + r\) maps each coordinator state to a non‑negative integer, where \(d\) is the
current recursion depth and \(r\) is the number of remaining phases.  Every state transition or
recursive call strictly decreases \(\phi\).

### Proof of Correctness

We prove by induction on the sequence of states that the coordinator produces a valid EDRR cycle.

**Base case**: At `expand` the context \(C\) contains the initial input.  After executing the
phase, \(C\) is updated with \(o_1\) and the invariant “`expand` completed” holds.

**Inductive step**: Assume after phase \(k\) the context contains results \(o_1,\dots,o_k\) and the
coordinator is in state \(s_k\).  The transition function \(\delta\) allows only \(s_{k+1}\) as the
next state.  Executing \(s_{k+1}\) yields \(o_{k+1}\); applying \(\mu\) preserves previous outputs
and appends \(o_{k+1}\).  Thus the invariant extends to \(k+1\).  By induction, after
`retrospect` the coordinator reaches `completed` with context containing all phase results.

### Proof of Convergence

The variant function \(\phi\) is an element of the well‑founded set \(\mathbb{N}\).  Each state
transition reduces \(r\) by one, and each micro‑cycle increases \(d\) but is bounded by
\(d_{\max}\).  Therefore \(\phi\) decreases on every transition and cannot decrease indefinitely.
Thus the coordinator terminates in finite steps, guaranteeing convergence of each EDRR cycle.

## Acceptance Criteria

- The coordinator enforces the `expand → differentiate → refine → retrospect` order.
- Context updates are deterministic and idempotent across phases.
- Recursive micro‑cycles never exceed the configured depth \(d_{\max}\).
- The coordinator terminates with status `completed` and a consolidated context.

## Implementation Notes

- Runtime logic resides in [`src/devsynth/application/edrr/coordinator/core.py`](../../src/devsynth/application/edrr/coordinator/core.py) with persistence and phase-management mixins in [`persistence.py`](../../src/devsynth/application/edrr/coordinator/persistence.py) and [`phase_management.py`](../../src/devsynth/application/edrr/coordinator/phase_management.py).
- Manifest-driven execution and template hydration leverage [`src/devsynth/application/edrr/manifest_parser.py`](../../src/devsynth/application/edrr/manifest_parser.py), exercised end-to-end by the behavior suites referenced above.
- Threshold sanitation and recursion bounds are derived from [`docs/implementation/edrr_invariants.md`](../implementation/edrr_invariants.md) and validated through [`tests/unit/application/edrr/test_threshold_helpers.py`](../../tests/unit/application/edrr/test_threshold_helpers.py).
