# Test Collection Regressions — 2025-10-04

Title: Test collection regressions — CLI progress, memory protocols, behavior assets
Date: 2025-10-04 16:30 UTC
Status: open
Affected Area: tests

## Reproduction
- `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
- `poetry run pytest --collect-only -q`

## Exit Codes
- `devsynth run-tests`: 1 (collection failure)
- `pytest --collect-only`: 130 (interrupted after surfacing 61 collection errors for triage)

## Artifacts
- `logs/devsynth.log`
- `diagnostics/pytest_collect_unit_fast_20251004T061503Z.log`
- `diagnostics/mypy_strict_src_devsynth_20251004T155204Z.txt` (typing baseline)

## Observations
- `_ProgressIndicatorBase` and related helpers are no longer exported, so CLI long-running progress tests raise `NameError` during import.【9ecea8†L1-L88】
- `devsynth.memory.sync_manager` declares `Protocol["ValueT"]`, which is rejected at runtime, causing TypeError in every SyncManager-dependent suite.【9ecea8†L41-L84】
- 2025-10-04: `MemoryStore` now declares `Protocol[ValueT]` with runtime-compatible generics; targeted unit tests cover typed stores and rollback flows.【F:src/devsynth/memory/sync_manager.py†L1-L73】【F:tests/unit/memory/test_sync_manager_protocol_runtime.py†L1-L76】
- `tests/unit/interface/conftest.py` defines `pytest_plugins`, which pytest 8+ no longer supports outside the top-level conftest; collection aborts before tests run.【9ecea8†L57-L76】
- Behavior suites reference `.feature` files that are missing from the repository (UXBridge/WebUI flow files under `tests/behavior/general/`).【9ecea8†L120-L164】
- Optional backend smoke tests (Chromadb, Faiss, Kuzu) import drivers eagerly rather than respecting `requires_resource` markers, raising `ValueError` when extras are not installed.【9ecea8†L96-L120】
- Repository-wide `pytestmark` auto-injection placed markers inside import tuples; Python now raises `SyntaxError: invalid syntax` before tests collect.【d62a9a†L12-L33】
- Integration modules such as `test_deployment_automation.py` declare `pytestmark` without importing pytest, triggering `NameError` at import time.【e85f55†L1-L22】
- WebUI BDD suites still load `general/*.feature` rather than `features/general/*.feature`, producing `FileNotFoundError` for assets that exist under the features directory.【6cd789†L12-L28】
- 2025-10-06: Fast+medium rehearsal aborts before collection because pytest registers `pytest_bdd` twice when nested `pytest_plugins` exports load the plugin in both interface-level and root-level contexts.【F:logs/devsynth_run-tests_fast_medium_20251006T033632Z.log†L1-L84】

## Next Actions
- [ ] Restore `_ProgressIndicatorBase` exports (likely `devsynth.application.cli.long_running_progress`) and ensure tests import helpers from supported modules.
- [x] Rework `MemoryStore` and related Protocol definitions to use proper `TypeVar` generics; add unit tests to prove runtime + mypy compatibility.
- [ ] Move `pytest_plugins` declarations into the repository root `conftest.py` or convert to plugin registration helpers, then capture a clean `pytest --collect-only -q` transcript replacing the 2025-10-06 failure log.【F:logs/devsynth_run-tests_fast_medium_20251006T033632Z.log†L1-L84】
- [ ] Recreate or relocate the missing `.feature` files referenced by behavior suites; update loaders and traceability documents accordingly.
- [ ] Guard optional backend tests with `pytest.importorskip` plus `requires_resource` flags so they skip cleanly without extras.
- [ ] Sweep unit/domain suites to move `pytestmark` statements outside import contexts and rerun targeted `pytest -k nothing` checks to prove SyntaxErrors are gone.【d62a9a†L12-L33】
- [ ] Add explicit `import pytest` lines (or remove unused `pytestmark`) in integration suites to prevent import-time NameErrors.【e85f55†L1-L22】
- [ ] Update `pytest_bdd.scenarios(...)` paths to reference `features/general/*.feature` and capture refreshed traceability manifests.【6cd789†L12-L28】
- [ ] Re-run smoke and `--collect-only` commands, attaching new logs when failures cease.

## Resolution Evidence
- 2025-10-04: Smoke command still fails pending broader regression fixes; captured output in `logs/devsynth_run-tests_smoke_fast_20251004T201351Z.log`.
- 2025-10-04: `poetry run pytest tests/unit/application/cli/test_long_running_progress.py tests/unit/memory/test_sync_manager_protocol_runtime.py -q` passes locally after restoring `_ProgressIndicatorBase` exports and SyncManager generics.
- 2025-10-07: `poetry run pytest --collect-only -q` completes without duplicate `pytest_bdd` registration; see `logs/pytest_collect_only_20251007.log` for the full transcript (warnings highlight legacy suites missing speed markers).

```
$ poetry run pytest tests/unit/application/cli/test_long_running_progress.py tests/unit/memory/test_sync_manager_protocol_runtime.py -q
======================================================= warnings summary =======================================================
.venv/lib/python3.12/site-packages/pydantic_core/core_schema.py:4137
.venv/lib/python3.12/site-packages/pydantic_core/core_schema.py:4137
  /workspace/devsynth/.venv/lib/python3.12/site-packages/pydantic_core/core_schema.py:4137: DeprecationWarning: `FieldValidationInfo` is deprecated, use `ValidationInfo` instead.
    warnings.warn(msg, DeprecationWarning, stacklevel=1)

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================================= Test Categorization Summary ==================================================
Test Type Distribution:
  Unit Tests: 12
  Integration Tests: 0
  Behavior Tests: 0

Test Speed Distribution:
  Fast Tests (< 1s): 12
  Medium Tests (1-5s): 0
  Slow Tests (> 5s): 0
===================================================== Top 10 Slowest Tests =====================================================
1. tests/unit/application/cli/test_long_running_progress.py::test_progress_indicator_base_alias_is_exported: 0.06s
2. tests/unit/memory/test_sync_manager_protocol_runtime.py::test_sync_manager_import_and_construction_succeeds: 0.01s
3. tests/unit/application/cli/test_long_running_progress.py::test_update_adapts_interval_and_checkpoints: 0.01s
4. tests/unit/application/cli/test_long_running_progress.py::test_subtask_checkpoint_spacing_respects_minimum: 0.01s
5. tests/unit/application/cli/test_long_running_progress.py::test_simulation_timeline_tracks_history_and_alias_renames: 0.01s
6. tests/unit/application/cli/test_long_running_progress.py::test_status_history_tracks_unique_status_changes: 0.01s
7. tests/unit/application/cli/test_long_running_progress.py::test_subtask_completion_rolls_up_and_freezes_summary: 0.01s
8. tests/unit/memory/test_sync_manager_protocol_runtime.py::test_transaction_rolls_back_typed_stores: 0.01s
9. tests/unit/application/cli/test_long_running_progress.py::test_simulation_timeline_produces_deterministic_transcript: 0.01s
10. tests/unit/application/cli/test_long_running_progress.py::test_summary_reflects_fake_timeline_and_sanitizes_descriptions: 0.01s
12 passed, 2 warnings in 0.83s
```
