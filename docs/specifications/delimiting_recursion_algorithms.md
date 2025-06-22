---
title: "Delimiting Recursion Algorithms"
date: "2025-06-16"
version: "0.1.0"
tags:
  - "specification"
  - "edrr"
  - "heuristics"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-16"
---

# Delimiting Recursion Algorithms

This specification describes heuristics for terminating recursive EDRR cycles. These algorithms ensure the system balances thorough exploration with resource constraints.

## Termination Heuristics

1. **Maximum Depth**
   - Abort recursion when `depth` exceeds a configurable limit.
2. **Granularity Threshold**
   - Skip recursion for tasks estimated below a complexity threshold.
3. **Cost Benefit Ratio**
   - Estimate potential benefit of another cycle versus expected cost. Stop when benefit drops below a defined ratio.
4. **Quality Plateau Detection**
   - Track quality metrics between cycles and stop when improvements fall below a minimum delta.
5. **Human Override**
   - Allow manual confirmation to continue or abort recursion when automated metrics are inconclusive.

These heuristics are referenced by `should_terminate` in the [Recursive EDRR Pseudocode](recursive_edrr_pseudocode.md).
