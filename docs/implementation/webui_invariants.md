---
author: DevSynth Team
date: '2025-09-17'
status: published
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

`WizardState.go_to_step` normalizes the requested step to the valid range `[1, total_steps]`, preserving state consistency. Property test `test_go_to_step_bounds` replays out-of-range navigation to confirm the clamp behavior.【F:tests/property/test_webui_properties.py†L22-L31】

```python
from devsynth.interface.webui_state import WizardState

state = WizardState("wizard", steps=5)
state.go_to_step(7)
assert state.get_current_step() == 5
```

## Completion Convergence

Repeatedly calling `next_step` eventually reaches the final step, after which subsequent calls are idempotent. Property test `test_next_step_converges_to_completion` iterates beyond the end of the wizard and asserts the terminal step persists.【F:tests/property/test_webui_properties.py†L34-L44】

```python
from devsynth.interface.webui_state import WizardState

state = WizardState("wizard", steps=3)
for _ in range(5):
    state.next_step()
assert state.get_current_step() == state.get_total_steps()
```

This behavior is exercised by `tests/property/test_webui_properties.py::test_next_step_converges_to_completion`.

## Coverage Signal (2025-09-20)

- **Targeted Streamlit harnesses:** Focused fast suites [`tests/unit/interface/test_webui_targeted_branches.py`](../../tests/unit/interface/test_webui_targeted_branches.py) and [`tests/unit/interface/test_webui_bridge_targeted.py`](../../tests/unit/interface/test_webui_bridge_targeted.py) drive question prompts, error tracebacks, highlight routing, and progress threshold transitions without a real Streamlit installation. Running `poetry run pytest … --cov=devsynth.interface.webui --cov=devsynth.interface.webui_bridge` captures 22 % line coverage for each module, as recorded in [`issues/tmp_cov_webui.json`](../../issues/tmp_cov_webui.json) and [`issues/tmp_cov_webui_bridge.json`](../../issues/tmp_cov_webui_bridge.json), establishing a measurable floor while documenting remaining rendering gaps for follow-up.【F:issues/tmp_cov_webui.json†L1-L1】【F:issues/tmp_cov_webui_bridge.json†L1-L1】

## Coverage Signal (2025-09-17)

- **Property-driven sweep:** `DEVSYNTH_PROPERTY_TESTING=true poetry run coverage run -m pytest --override-ini addopts="" tests/property/test_webui_properties.py` executes the navigation properties without requiring the optional Streamlit dependency and persists artifacts at `test_reports/webui_state_coverage.json` and `test_reports/htmlcov_webui_state/index.html` for audit trails.【52a70d†L1-L17】
- **Measured coverage:** The focused run exercises 70 of 134 statements (52.24 % line coverage) in `src/devsynth/interface/webui_state.py`, confirming the bounded navigation invariants while flagging remaining Streamlit-dependent branches for future work.【a9203c†L1-L9】
- **Limitations:** The broader unit suite still requires the optional `webui` extra (Streamlit); until that dependency is vendored into CI, rely on the property harness above for quick regression checks.

## Traceability

- Specification: [docs/specifications/webui-integration.md](../../docs/specifications/webui-integration.md) defines wizard state normalization and completion requirements.【F:docs/specifications/webui-integration.md†L1-L40】
- Behavior coverage: [tests/behavior/features/webui/requirements_wizard_with_state.feature](../../tests/behavior/features/webui/requirements_wizard_with_state.feature) demonstrates multi-step navigation, completion, and error handling flows that rely on these invariants.【F:tests/behavior/features/webui/requirements_wizard_with_state.feature†L1-L66】
- Property coverage: [tests/property/test_webui_properties.py](../../tests/property/test_webui_properties.py) randomizes bounds and convergence behaviors for the `WizardState` navigation API.【F:tests/property/test_webui_properties.py†L22-L44】

## References

- Issue: [issues/webui-integration.md](../issues/webui-integration.md)
- Test: [tests/property/test_webui_properties.py](../tests/property/test_webui_properties.py)
