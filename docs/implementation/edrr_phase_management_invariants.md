---
author: DevSynth Team
date: '2025-09-16'
status: draft
tags:
- implementation
- invariants
title: EDRR Phase Management Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; EDRR Phase Management Invariants
</div>

# EDRR Phase Management Invariants

This note captures the invariants enforced by the phase-management helpers that
back the coordinator orchestration logic.

## Manifest Dependencies Gate Transitions

`progress_to_phase` consults the manifest parser before any transition. If a
phase's prerequisites are missing it raises `EDRRCoordinatorError`, preventing
the coordinator from skipping required work.【F:src/devsynth/application/edrr/coordinator/phase_management.py†L33-L42】

```python
from unittest.mock import MagicMock

from devsynth.application.edrr.coordinator import EDRRCoordinator, EDRRCoordinatorError
from devsynth.methodology.base import Phase

coordinator = EDRRCoordinator(
    memory_manager=MagicMock(),
    wsde_team=MagicMock(),
    code_analyzer=MagicMock(),
    ast_transformer=MagicMock(),
    prompt_manager=MagicMock(),
    documentation_manager=MagicMock(),
)
coordinator.manifest = {}
coordinator.manifest_parser = MagicMock()
coordinator.manifest_parser.check_phase_dependencies.return_value = False

try:
    coordinator.progress_to_phase(Phase.DIFFERENTIATE)
except EDRRCoordinatorError:
    pass
else:
    raise AssertionError("Dependency check should fail")
```

## Role Synchronization and Context Persistence

When a transition succeeds the mixin rotates Primus, stores the new role map,
persists phase metadata, and records the start timestamp. Preserved context is
merged with any stored snapshot before being saved again, ensuring subsequent
phases can recover prior results.【F:src/devsynth/application/edrr/coordinator/phase_management.py†L56-L130】

## Deterministic Next-Phase Decisions

`_decide_next_phase` honors manual overrides first, then quality thresholds, and
finally elapsed timeouts. Only when all guards pass does it advance to the next
phase in sequence.【F:src/devsynth/application/edrr/coordinator/phase_management.py†L162-L210】

```python
from devsynth.application.edrr.coordinator import PhaseManagementMixin
from devsynth.methodology.base import Phase


class DemoCoordinator(PhaseManagementMixin):
    def __init__(self) -> None:
        self.manual_next_phase = Phase.REFINE
        self.auto_phase_transitions = True
        self.current_phase = Phase.DIFFERENTIATE
        self.results = {"DIFFERENTIATE": {"phase_complete": True}}
        self._phase_start_times = {}
        self.phase_transition_timeout = 10

    def _get_phase_quality_threshold(self, phase: Phase) -> float | None:
        return None


demo = DemoCoordinator()
assert demo._decide_next_phase() == Phase.REFINE
```

## Bounded Auto-Progression

`_maybe_auto_progress` only triggers when auto transitions are enabled and the
team implements elaboration. It repeatedly asks `_decide_next_phase` for the next
phase, stopping after at most ten iterations to avoid runaway loops.【F:src/devsynth/application/edrr/coordinator/phase_management.py†L212-L223】

## References

- Tests: `tests/unit/application/edrr/test_phase_management_module.py`
- Specification: [docs/specifications/edrr_cycle_specification.md](../specifications/edrr_cycle_specification.md)
