---

title: "Delimiting Recursion Algorithms"
date: "2025-06-16"
version: "0.1.0a1"
tags:
  - "specification"
  - "EDRR"
  - "heuristics"

references:
  - "Cormen, T. H., C. E. Leiserson, R. L. Rivest, and C. Stein. Introduction to Algorithms. 4th ed., MIT Press, 2022."

status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; Delimiting Recursion Algorithms
</div>

# Delimiting Recursion Algorithms

This specification describes heuristics for terminating recursive EDRR cycles.
They mirror the logic in `EDRRCoordinator.should_terminate_recursion`, ensuring
the system balances exploration with cost and quality constraints.

## Termination Heuristics

1. **Maximum Depth**
   - Recursion is aborted when `recursion_depth` reaches `DEFAULT_MAX_RECURSION_DEPTH`.
2. **Granularity Threshold**
   - If a task provides `granularity_score` below `DEFAULT_GRANULARITY_THRESHOLD`

     the coordinator skips creating a micro cycle.

3. **Cost Benefit Ratio**
   - When both `cost_score` and `benefit_score` are supplied, their ratio is compared

     against `DEFAULT_COST_BENEFIT_RATIO`. Higher values terminate recursion.

4. **Quality Threshold**
   - A `quality_score` exceeding `DEFAULT_QUALITY_THRESHOLD` indicates sufficient

     quality, so further recursion is not pursued.

5. **Resource Limit**
   - If `resource_usage` surpasses `DEFAULT_RESOURCE_LIMIT` the cycle stops to

     conserve resources.

6. **Human Override**
   - A task may include `human_override` with values `"terminate"` or

     `"continue"` to explicitly control recursion.

## Proof of Termination

Each heuristic places an upper bound on recursion depth or cost. With finite
inputs, at least one threshold will eventually be met, guaranteeing that the
EDRR cycle halts. Unit test `tests/unit/application/edrr/test_enhanced_recursion_termination.py`
and integration test `tests/integration/general/test_recursive_recovery_flow.py`
exercise these termination paths.

These heuristics are implemented in `EDRRCoordinator.should_terminate_recursion`
and referenced in the [Recursive EDRR Pseudocode](recursive_edrr_pseudocode.md).

## Security Considerations

Configuration values for recursion limits and thresholds are validated. Invalid or
out-of-range settings fall back to safe defaults, preventing attempts to bypass
recursion controls.

## Implementation Status

This feature is **implemented**. The heuristics are available in `src/devsynth/application/edrr/coordinator/core.py`.

## What proofs confirm the solution?
- BDD scenarios in [`tests/behavior/features/delimiting_recursion_algorithms.feature`](../../tests/behavior/features/delimiting_recursion_algorithms.feature) ensure termination and expected outcomes.
- Finite state transitions and bounded loops guarantee termination.
