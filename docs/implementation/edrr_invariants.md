---
author: DevSynth Team
date: '2025-09-21'
status: review
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

## References

- Specification: [docs/specifications/edrr_cycle_specification.md](../specifications/edrr_cycle_specification.md)
- BDD Feature: [tests/behavior/features/edrr_cycle_specification.feature](../tests/behavior/features/edrr_cycle_specification.feature)
- Issue: [issues/edrr-invariants.md](../issues/edrr-invariants.md)

## Evidence (2025-09-21)

- Unit tests: `tests/unit/application/edrr/test_threshold_helpers.py::{test_sanitize_positive_int_handles_out_of_range,test_sanitize_threshold_clamps_invalid_values,test_get_phase_quality_threshold_respects_config,test_get_phase_quality_threshold_returns_none_when_missing,test_get_micro_cycle_config_sanitizes_values}` confirm the helper invariants and sanitized recursive micro-cycle configuration.
- Regression coverage confirms the coordinator now imports templates from `devsynth.application.edrr.templates` during construction, allowing helper tests to execute without ModuleNotFoundError.
