---
title: "EDRR Recursion Termination"
date: "2025-05-09"
version: "0.1.0-alpha.1"
tags:
  - "specification"
  - "EDRR"
  - "recursion"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-05-09"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; EDRR Recursion Termination
</div>

# EDRR Recursion Termination

This specification captures invariants and termination criteria for recursive
EDRR cycles managed by the coordinator.

## Invariants

- The coordinator enforces a default maximum recursion depth of three and
  sanitizes the configured limit before use【F:src/devsynth/application/edrr/coordinator.py†L88-L97】【F:src/devsynth/application/edrr/coordinator.py†L235-L238】
- Micro cycles may only be created when the current depth is below the maximum;
  attempts beyond that bound raise an error【F:src/devsynth/application/edrr/coordinator.py†L960-L968】

## Termination Conditions

Recursion halts when any of the following criteria evaluated by
`should_terminate_recursion` are satisfied【F:src/devsynth/application/edrr/coordinator.py†L1072-L1099】:

1. Human override directives
2. Granularity falls below the threshold
3. Cost outweighs benefit
4. Quality already meets requirements
5. Resource usage exceeds configured limits
6. Complexity exceeds permissible bounds
7. Results have converged
8. Diminishing returns on further recursion
9. Incompatibility with parent phase
10. Historical ineffectiveness for similar tasks
11. Maximum recursion depth reached
12. Time limit exceeded
13. Memory usage exceeds limits
14. Approaching any of the above limits
15. Combined moderate factors indicating termination

These rules guarantee that recursive exploration remains bounded and
predictable.

## Acceptance Criteria

- Documentation aligns with coordinator invariants.
- Tests assert depth bounds and termination triggers.
