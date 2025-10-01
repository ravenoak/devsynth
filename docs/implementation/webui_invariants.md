---
author: DevSynth Team
date: '2025-10-01'
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

## Bridge Wizard Clamps and Lazy Loader

Fast suites now exercise the WebUI bridge directly so wizard navigation mirrors the CLI clamps without requiring the optional Streamlit extra. `_require_streamlit` caches the injected stub on first import and surfaces the install command when the dependency is missing,【F:tests/unit/interface/test_webui_bridge_fast_suite.py†L214-L247】 while `adjust_wizard_step` and `normalize_wizard_step` warn on invalid totals, directions, or values before clamping into range.【F:tests/unit/interface/test_webui_bridge_fast_suite.py†L250-L271】 Complementary unit coverage reloads `devsynth.interface.webui` with a deterministic Streamlit stub to prove the lazy loader only imports once, converts rich markup to HTML, and records wizard warnings when callers supply malformed inputs, aligning with the Streamlit-free BDD scenarios.【F:tests/unit/interface/test_webui_lazy_streamlit_and_wizard.py†L1-L81】 The same fast harness proves that `display_result` continues to route through `OutputFormatter` and that highlight messages fall back to `st.write` when `st.info` is unavailable, maintaining parity with CLI formatting expectations.【F:tests/unit/interface/test_webui_bridge_fast_suite.py†L274-L359】 Targeted simulations extend this coverage by calling the new deterministic harnesses: `tests/unit/interface/test_webui_simulations_fast.py` drives `_UIProgress` updates, sanitized error rendering, and wizard clamps entirely under the stubbed Streamlit runtime so both the WebUI module and bridge exercise their optional dependency fallbacks.【F:tests/unit/interface/test_webui_simulations_fast.py†L46-L174】

Focused Streamlit-free regressions now patch both `_STREAMLIT` and `webui_bridge.st` to deterministic recorders, proving the lazy loader's install guidance, sanitised message routing, nested `WebUIProgressIndicator` lifecycle, ETA formatting, and wizard clamps without importing the real dependency.【F:tests/unit/interface/test_webui_streamlit_free_regressions.py†L404-L552】 These tests demonstrate that script tags are stripped before the bridge or UI forwards results, hierarchical subtasks stay escaped through completion, and malformed wizard navigation requests are clamped defensively.

## Coverage Signal (2025-10-01)

- **Streamlit-free regression harness:** `pytest --cov=devsynth.interface.webui --cov=devsynth.interface.webui_bridge --cov-report=term-missing --cov-fail-under=0 tests/unit/interface/test_webui_streamlit_free_regressions.py` records 18.27 % coverage for `webui.py` and 25.37 % for `webui_bridge.py`, confirming the sanitized display branches, progress ETA formatting, and wizard clamps exercised by the new stubbed suite. Artefacts and the raw report are stored under `issues/tmp_artifacts/webui/20251001T035910Z/` for traceability.【F:issues/tmp_artifacts/webui/20251001T035910Z/coverage.log†L20-L24】

## Coverage Signal (2025-09-30)

- **Deterministic progress simulations:** `poetry run pytest tests/unit/interface/test_webui_simulations_fast.py --maxfail=1 --cov=devsynth.interface.webui --cov=devsynth.interface.webui_bridge --cov-report=term --cov-fail-under=0` drives the new deterministic harnesses that exercise `_require_streamlit`, `_UIProgress`, sanitized error routing, and wizard clamps without importing Streamlit. Artefacts documenting the focused run live under `issues/tmp_artifacts/webui_progress_simulations/20250930T214900Z/` for traceability.【F:issues/tmp_artifacts/webui_progress_simulations/20250930T214900Z/notes.md†L1-L5】
- **Historical harnesses (2025-09-20):** Focused fast suites [`tests/unit/interface/test_webui_targeted_branches.py`](../../tests/unit/interface/test_webui_targeted_branches.py) and [`tests/unit/interface/test_webui_bridge_targeted.py`](../../tests/unit/interface/test_webui_bridge_targeted.py) continue to drive question prompts, error tracebacks, highlight routing, and progress threshold transitions without a real Streamlit installation. Running `poetry run pytest … --cov=devsynth.interface.webui --cov=devsynth.interface.webui_bridge` captured 22 % line coverage for each module, as recorded in [`issues/tmp_cov_webui.json`](../../issues/tmp_cov_webui.json) and [`issues/tmp_cov_webui_bridge.json`](../../issues/tmp_cov_webui_bridge.json), establishing a measurable floor while documenting remaining rendering gaps for follow-up.【F:issues/tmp_cov_webui.json†L1-L1】【F:issues/tmp_cov_webui_bridge.json†L1-L1】

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
