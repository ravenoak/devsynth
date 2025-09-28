---
author: DevSynth Team
date: '2025-09-21'
last_reviewed: '2025-09-23'
status: published
tags:
- implementation
- invariants
title: EDRR Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; EDRR Invariants
</div>

# EDRR Invariants

This note records invariants of the EDRR coordinator's configuration helpers.

## Bounded Positive Integers

`_sanitize_positive_int` clamps arbitrary inputs to the range [1, max].

```python
from devsynth.application.edrr.coordinator import EDRRCoordinator

assert EDRRCoordinator._sanitize_positive_int(-5, 1) == 1
assert EDRRCoordinator._sanitize_positive_int(12, 1, max_value=10) == 1
assert EDRRCoordinator._sanitize_positive_int(3, 1) == 3
```

## Normalized Thresholds

`_sanitize_threshold` keeps quality thresholds within [0.0, 1.0].

```python
from devsynth.application.edrr.coordinator import EDRRCoordinator

assert EDRRCoordinator._sanitize_threshold(2.0, 0.7) == 0.7
assert EDRRCoordinator._sanitize_threshold(-1.0, 0.7) == 0.7
assert EDRRCoordinator._sanitize_threshold(0.8, 0.7) == 0.8
```

These helpers guarantee that `_get_micro_cycle_config` returns finite iteration counts and valid quality thresholds, ensuring that recursive EDRR cycles terminate.

## Recursive Phase Progression

`progress_to_phase` couples macro and micro runs by persisting child context before invoking `_maybe_auto_progress`. When the Expand phase records `{"phase_complete": True, "quality_score": 0.96}`, automatic transitions advance to Differentiate and then Refine while copying the micro-cycle ledger keyed by cycle ID. The run halts in Refine once its quality score (0.42 in the simulation) falls below the 0.9 threshold, populating `quality_issues` and `additional_processing` so manual intervention can resume the loop. The task labels are read directly from `tests/behavior/features/recursive_edrr_coordinator.feature`, keeping the expectations synchronized with the BDD narrative.

## Recursion Depth Guard

`create_micro_cycle` raises `EDRRCoordinatorError` with `"Maximum recursion depth"` when a level-3 cycle (depth 3 with the default configuration) attempts to spawn a level-4 descendant. The guard executes before appending to `child_cycles`, so the failed attempt leaves the recursion tree unchanged while surfacing the reason string for audit trails.

Behavior coverage exercises the same guard and the `should_terminate_recursion` helper directly, asserting that the BDD narrative in `tests/behavior/features/edrr_recursion_termination.feature` triggers the high-severity `max_depth` factor while still honoring explicit human overrides to continue recursion.【F:tests/behavior/features/edrr_recursion_termination.feature†L1-L15】【F:tests/behavior/test_progress_failover_and_recursion.py†L132-L166】【F:src/devsynth/application/edrr/coordinator/core.py†L640-L731】【F:src/devsynth/application/edrr/coordinator/core.py†L1038-L1085】

## Recovery Diagnostics

`_attempt_recovery` now reports retry failures by returning `{"recovered": False, "reason": ...}` whenever the delegated phase executor raises again. This ensures error hooks can record the terminal exception, reinforcing the dialectical auditing pipeline when retries cannot salvage a phase.

## References

- Specification: [docs/specifications/edrr_cycle_specification.md](../specifications/edrr_cycle_specification.md)
- Specification: [docs/specifications/edrr-coordinator.md](../specifications/edrr-coordinator.md)
- BDD Feature: [tests/behavior/features/edrr_cycle_specification.feature](../tests/behavior/features/edrr_cycle_specification.feature)
- Issue: [issues/edrr-invariants.md](../issues/edrr-invariants.md)

## Evidence (2025-09-23)

- Unit tests: `tests/unit/application/edrr/test_threshold_helpers.py::{test_coordinator_registers_templates,test_assess_phase_quality_uses_config_threshold,test_micro_cycle_config_sanitization,test_sanitize_positive_int_handles_out_of_range,test_sanitize_threshold_clamps_invalid_values,test_get_phase_quality_threshold_respects_config,test_get_phase_quality_threshold_returns_none_when_missing,test_get_micro_cycle_config_sanitizes_values}` confirm template hydration and helper invariants, matching the sanitization rules documented above.
- New simulations: `tests/unit/application/edrr/test_coordinator_macro_micro_simulation.py::{test_phase_transitions_follow_recursive_feature,test_recursion_depth_limit_matches_feature,test_failed_retry_reports_reason}` exercise automatic phase progress, recursion guards, and recovery diagnostics against the BDD-driven task set, establishing the additional invariants described in this note.
- The EDRR coordinator now depends on the lightweight `SupportsTemplateRegistration` protocol from `devsynth.application.edrr.templates`, preventing ModuleNotFoundError during helper tests while keeping template wiring aligned with the coordinator specification.
