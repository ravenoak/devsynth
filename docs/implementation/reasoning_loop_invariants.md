---
author: DevSynth Team
date: '2025-09-12'
status: draft
tags:
- implementation
- invariants
title: Reasoning Loop Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Reasoning Loop Invariants
</div>

# Reasoning Loop Invariants

This note outlines invariants of `reasoning_loop` and demonstrates convergence.

## Phase Convergence

The deterministic transition map
`{expand→differentiate, differentiate→refine, refine→refine}` guarantees that
repeated iterations without an explicit `next_phase` reach `refine` in at most
two steps.

```python
from devsynth.methodology.edrr.reasoning_loop import Phase

transition = {Phase.EXPAND: Phase.DIFFERENTIATE,
              Phase.DIFFERENTIATE: Phase.REFINE,
              Phase.REFINE: Phase.REFINE}

phase = Phase.EXPAND
for _ in range(3):
    phase = transition[phase]
assert phase is Phase.REFINE
```

## Synthesis Propagation

If iteration *i* produces `synthesis_i`, the next iteration receives
`task['solution'] == synthesis_i`, ensuring monotonic refinement of the task
state.

This behavior is verified by
`tests/property/test_reasoning_loop_properties.py::test_reasoning_loop_propagates_synthesis`.

## References

- Issue: [issues/Finalize-dialectical-reasoning.md](../issues/Finalize-dialectical-reasoning.md)
- Test: [tests/property/test_reasoning_loop_properties.py](../tests/property/test_reasoning_loop_properties.py)
