---
author: AI Assistant
date: '2025-09-16'
status: active
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

`_decide_next_phase` honours manual overrides first, then quality thresholds,
and finally elapsed timeouts. Only when all guards pass does it advance to the
next phase in sequence.【F:src/devsynth/application/edrr/coordinator/phase_management.py†L162-L210】

The decision routine also enforces the following safeguards:

- Manual overrides are consumed exactly once, preventing stale selections from
  leaking into later decisions. See
  [`test_decide_next_phase_consumes_manual_override`](../../tests/unit/application/edrr/test_phase_management_module.py).
- Automatic transitions require `auto_phase_transitions` to be enabled; when it
  is disabled the coordinator holds position even if the current phase has been
  marked complete. Verified by
  [`test_decide_next_phase_requires_auto_transitions`](../../tests/unit/application/edrr/test_phase_management_module.py).
- The RETROSPECT phase terminates the sequence—automatic routing returns
  ``None`` and explicit advancement raises `EDRRCoordinatorError`. Guarded by
  [`test_decide_next_phase_returns_none_for_final_phase`](../../tests/unit/application/edrr/test_phase_management_module.py)
  and
  [`test_progress_to_next_phase_rejects_final_phase`](../../tests/unit/application/edrr/test_phase_management_module.py).

## Bounded Auto-Progression

`_maybe_auto_progress` only triggers when auto transitions are enabled and the
team implements elaboration. It repeatedly asks `_decide_next_phase` for the next
phase, stopping after at most ten iterations to avoid runaway loops.【F:src/devsynth/application/edrr/coordinator/phase_management.py†L212-L223】

## References

- Tests: `tests/unit/application/edrr/test_phase_management_module.py`
- Specification: [docs/specifications/edrr_cycle_specification.md](../specifications/edrr_cycle_specification.md)
