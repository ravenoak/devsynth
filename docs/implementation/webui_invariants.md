---
author: DevSynth Team
date: '2025-09-13'
status: draft
tags:
- implementation
- invariants
title: WebUI State Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; WebUI State Invariants
</div>

# WebUI State Invariants

This note outlines invariants of WebUI page state management and demonstrates convergence of step navigation.

## Bounded Step Navigation

`WizardState.go_to_step` normalizes the requested step to the valid range `[1, total_steps]`, preserving state consistency.

```python
from devsynth.interface.webui_state import WizardState

state = WizardState("wizard", steps=5)
state.go_to_step(7)
assert state.get_current_step() == 5
```

## Completion Convergence

Repeatedly calling `next_step` eventually reaches the final step, after which subsequent calls are idempotent.

```python
from devsynth.interface.webui_state import WizardState

state = WizardState("wizard", steps=3)
for _ in range(5):
    state.next_step()
assert state.get_current_step() == state.get_total_steps()
```

This behavior is exercised by `tests/property/test_webui_properties.py::test_next_step_converges_to_completion`.

## References

- Issue: [issues/webui-integration.md](../issues/webui-integration.md)
- Test: [tests/property/test_webui_properties.py](../tests/property/test_webui_properties.py)
