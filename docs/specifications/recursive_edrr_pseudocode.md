---
title: "Recursive EDRR Pseudocode"
date: "2025-06-16"
version: "0.1.0"
tags:
  - "specification"
  - "edrr"
  - "pseudocode"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-16"
---

# Recursive EDRR Pseudocode

This document outlines the pseudocode for orchestrating recursive EDRR cycles. It focuses on the main function signatures and how control flows between nested cycles.

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
```

## Recursion Flow

1. **run_cycle** begins with the current context and recursion `depth`.
2. **should_terminate** checks if recursion should stop, based on heuristics described in [Delimiting Recursion Algorithms](delimiting_recursion_algorithms.md).
3. Each phase (expand, differentiate, refine, retrospect) transforms the context.
4. The **retrospect** phase may spawn subtasks. For each subtask, `run_cycle` recurses with a child context and increased `depth`.
5. Results propagate back up the call stack once termination conditions are met.

For more background on the EDRR methodology, see the [EDRR Cycle Specification](edrr_cycle_specification.md).
