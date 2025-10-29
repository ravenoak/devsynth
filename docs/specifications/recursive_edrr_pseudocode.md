---

title: "Recursive EDRR Pseudocode"
date: "2025-06-16"
version: "0.1.0a1"
tags:
  - "specification"
  - "EDRR"
  - "pseudocode"

references:
  - "Cormen, T. H., C. E. Leiserson, R. L. Rivest, and C. Stein. Introduction to Algorithms. 4th ed., MIT Press, 2022."

status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Recursive EDRR Pseudocode
</div>

# Recursive EDRR Pseudocode

This document outlines the pseudocode for orchestrating recursive EDRR cycles.
It summarizes the logic implemented in `EDRRCoordinator`, the class that
manages the EDRR workflow. The coordinator can
spawn micro cycles within each phase and aggregates their results back into the
parent cycle.

## Core Functions

```pseudocode
function run_cycle(context, depth = 0) -> CycleResult:
    if should_terminate(context, depth):
        return finalize_cycle(context)

    expanded = expand(context)
    differentiated = differentiate(expanded)
    refined = refine(differentiated)
    retrospected = retrospect(refined)

    for subtask in retrospected.spawned_subtasks:
        child_context = context.create_child(subtask)
        run_cycle(child_context, depth + 1)

    return retrospected
```

```pseudocode
function expand(context) -> Context:
    // gather ideas and options
```

```pseudocode
function differentiate(context) -> Context:
    // evaluate and narrow options
```

```pseudocode
function refine(context) -> Context:
    // implement the chosen approach
```

```pseudocode
function retrospect(context) -> Context:
    // capture lessons learned and spawn follow-ups
```

```text

## Recursion Flow

1. **run_cycle** begins with the current context and recursion `depth`.
2. **should_terminate** checks if recursion should stop, based on heuristics described in [Delimiting Recursion Algorithms](delimiting_recursion_algorithms.md).
3. Each phase (expand, differentiate, refine, retrospect) transforms the context.
4. The **retrospect** phase may spawn subtasks. For each subtask, `run_cycle` recurses with a child context and increased `depth`.
5. Results propagate back up the call stack once termination conditions are met.


For more background on the EDRR methodology, see the [EDRR Specification](edrr_cycle_specification.md).

## Micro Cycle Creation

`EDRRCoordinator.create_micro_cycle` encapsulates the recursion logic:

```pseudocode

function create_micro_cycle(task, parent_phase) -> EDRRCoordinator:
    if recursion_depth >= DEFAULT_MAX_RECURSION_DEPTH:
        raise Error("Maximum recursion depth exceeded")
    if should_terminate_recursion(task):
        raise Error("Recursion terminated based on heuristics")

    micro = EDRRCoordinator(
        memory_manager,
        wsde_team,
        ...,
        recursion_depth + 1,
        parent_phase = parent_phase
    )

    micro.start_cycle(task)
    child_cycles.append(micro)
    store_micro_cycle_results(micro)
    return micro

```

The coordinator checks `should_terminate_recursion` before spawning a micro
cycle. If recursion proceeds, the child coordinator inherits the parent's
dependencies and increments `recursion_depth`. Results from the micro cycle are
stored under the parent's phase data so the overall cycle reflects nested work.
## Complexity Analysis

Let \(b\) be the maximum number of subtasks spawned in the **retrospect** phase
and \(d\) the maximum recursion depth. The number of cycle invocations is
bounded by \(O(b^d)\). Because each phase runs in linear time with respect to
its inputs, overall complexity is \(O(b^d)\). Unit tests such as
`tests/unit/application/edrr/test_recursive_edrr_coordinator.py` and behavior
tests like `tests/behavior/steps/test_recursive_edrr_coordinator_steps.py`
exercise this recursion and confirm termination behavior.

## Implementation Status

.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/recursive_edrr_pseudocode.feature`](../../tests/behavior/features/recursive_edrr_pseudocode.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
