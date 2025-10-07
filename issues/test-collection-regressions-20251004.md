# Test Collection Regressions — 2025-10-04

Title: Test collection regressions — CLI progress, memory protocols, behavior assets
Date: 2025-10-04 16:30 UTC
Status: open
Affected Area: tests

## Reproduction
- `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`
- `poetry run pytest --collect-only -q`
- `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 --dry-run`

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
- 2025-10-06 19:04 UTC: Captured `pytest --collect-only -q` after consolidating plugin exports; duplicate-registration errors are resolved but behavior steps still fail on indentation/`feature_path` bugs (52 collection errors remain).【F:logs/pytest_collect_only_20251006T190420Z.log†L1-L84】
- 2025-10-06 20:51 UTC: Targeted Agent API collections reproduced the indentation failures triggered by importing `feature_path` inside fixtures; both suites abort during module parsing.【F:diagnostics/testing/pytest_collect_agent_api_interactions_before_fix_20251006T205032Z.txt†L2-L61】【F:diagnostics/testing/pytest_collect_agent_api_health_metrics_before_fix_20251006T205115Z.txt†L2-L61】
- 2025-10-06 20:52 UTC: Hoisted the imports and restored a dedicated health-metrics aggregator so the scoped `scenarios(...)` calls resolve correctly; the `--collect-only` runs now enumerate all BDD-generated tests without error.【F:diagnostics/testing/pytest_collect_agent_api_interactions_after_fix_20251006T205132Z.txt†L1-L30】【F:diagnostics/testing/pytest_collect_agent_api_health_metrics_after_fix_20251006T205142Z.txt†L1-L25】
- 2025-10-06 21:02 UTC: Targeted `pytest --collect-only` run for the memory adapter steps fails because `tests/behavior/test_memory_adapter_read_and_write_operations.py` is missing; captured transcript at `diagnostics/pytest-collect-memory-adapter.log`.
- 2025-10-06 21:23–21:30 UTC: Full CLI reruns (`poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and `--speed=fast --speed=medium --report --no-parallel`) still abort during collection without emitting coverage artifacts or knowledge-graph IDs; see `logs/devsynth_run-tests_smoke_fast_20251006T212313Z.log` and `logs/devsynth_run-tests_fast_medium_20251006T212716Z.log`.【F:logs/devsynth_run-tests_smoke_fast_20251006T212313Z.log†L1-L9】【F:logs/devsynth_run-tests_fast_medium_20251006T212716Z.log†L1-L3】
- 2025-10-06 21:44–21:46 UTC: Manual smoke and fast+medium reruns now hang in `pytest --collect-only` with no further CLI output; new diagnostics record the running collector processes and the absence of refreshed artifacts before both commands were interrupted.【F:logs/devsynth_run-tests_smoke_fast_20251127T001200Z.log†L1-L6】【F:diagnostics/testing/devsynth_run_tests_smoke_fast_20251127T001200Z_summary.txt†L1-L11】【F:diagnostics/testing/devsynth_run_tests_fast_medium_20251127T002200Z_summary.txt†L1-L11】
- 2025-10-06 23:02 UTC: Behavior step imports collect cleanly after hoisting `feature_path` and `pytestmark` assignments; `poetry run pytest tests/behavior/steps/test_* --collect-only` enumerates 751 tests with 11 skips and no errors.【F:diagnostics/testing/devsynth_collect_behavior_steps_20251006T230221Z.log†L1-L14】
- 2025-10-06 23:05 UTC: Repository-wide `poetry run pytest -k nothing --collect-only` now completes without syntax/name errors, collecting 5,226 deselected items (34 skipped) across the suite.【F:diagnostics/testing/devsynth_collect_full_suite_20251006T230249Z.log†L1-L11】
- 2025-10-06 23:31 UTC: Rehydrated WebUI/UXBridge behavior features under `tests/behavior/features/general/` and reran the traceability + marker verifiers; manifests confirm the canonical paths resolve while remaining collection hygiene continues.【F:tests/behavior/features/general/webui_bridge.feature†L1-L9】【F:tests/behavior/features/general/complete_sprint_edrr_integration.feature†L1-L18】【F:diagnostics/verify_requirements_traceability_20251006T233102Z.txt†L1-L1】【F:diagnostics/verify_test_markers_20251006T233106Z.txt†L1-L1】
- 2025-10-07: `poetry run pytest tests/integration/memory -m fast --collect-only` on a workspace without memory extras now reports seven clean skips for ChromaDB-backed suites instead of raising import errors; deselected cases continue to honor speed markers while printing install guidance for developers.

## Next Actions
- [ ] Restore `_ProgressIndicatorBase` exports (likely `devsynth.application.cli.long_running_progress`) and ensure tests import helpers from supported modules.
- [x] Rework `MemoryStore` and related Protocol definitions to use proper `TypeVar` generics; add unit tests to prove runtime + mypy compatibility.
- [x] Move `pytest_plugins` declarations into the repository root `conftest.py` or convert to plugin registration helpers, then capture a clean `pytest --collect-only -q` transcript replacing the 2025-10-06 failure log (evidence: `logs/pytest_collect_only_20251006T190420Z.log`).【F:logs/devsynth_run-tests_fast_medium_20251006T033632Z.log†L1-L84】【F:logs/pytest_collect_only_20251006T190420Z.log†L1-L84】
- [x] Recreate or relocate the missing `.feature` files referenced by behavior suites; update loaders and traceability documents accordingly.【F:tests/behavior/features/general/webui_bridge.feature†L1-L9】【F:tests/behavior/features/general/complete_sprint_edrr_integration.feature†L1-L18】【F:diagnostics/verify_requirements_traceability_20251006T233102Z.txt†L1-L1】
- [ ] Guard optional backend tests with `pytest.importorskip` plus `requires_resource` flags so they skip cleanly without extras.
- [x] Sweep unit/domain suites to move `pytestmark` statements outside import contexts and rerun targeted `pytest -k nothing` checks to prove SyntaxErrors are gone.【d62a9a†L12-L33】【F:tests/integration/general/test_error_handling_at_integration_points.py†L7-L45】【F:tests/unit/application/memory/test_chromadb_store.py†L1-L58】【F:tests/behavior/steps/test_webui_integration_steps.py†L1-L58】【F:logs/pytest_collect_only_20251006T043523Z.log†L1-L113】
- [x] Add explicit `import pytest` lines (or remove unused `pytestmark`) in integration suites to prevent import-time NameErrors; audit confirmed affected modules now import pytest alongside relocated markers.【e85f55†L1-L22】【F:tests/integration/general/test_error_handling_at_integration_points.py†L7-L43】【F:tests/behavior/steps/test_webui_integration_steps.py†L1-L18】
- [x] Update `pytest_bdd.scenarios(...)` paths to reference `features/general/*.feature` and capture refreshed traceability manifests.【F:tests/behavior/test_webui_bridge.py†L1-L13】【F:tests/behavior/test_agent_api_interactions.py†L1-L10】【F:diagnostics/verify_test_markers_20251006T233106Z.txt†L1-L1】
- [ ] Re-run smoke, the smoke dry-run preview, and `--collect-only` commands, attaching new `diagnostics/` transcripts when failures cease.

## Resolution Evidence
- 2025-10-07: Plugin hoist landed; `pytest --collect-only -q` collects without duplicate registration, and the developer guide now documents the root-scope requirement in the new “Pytest plugin discipline” subsection.【F:logs/pytest_collect_only_20251007.log†L1-L40】【F:docs/developer_guides/test_execution_strategy.md†L161-L164】
- 2025-10-04: Smoke command still fails pending broader regression fixes; captured output in `logs/devsynth_run-tests_smoke_fast_20251004T201351Z.log`.
- 2025-10-04: `poetry run pytest tests/unit/application/cli/test_long_running_progress.py tests/unit/memory/test_sync_manager_protocol_runtime.py -q` passes locally after restoring `_ProgressIndicatorBase` exports and SyncManager generics.
- 2025-10-06 19:04 UTC: `poetry run pytest --collect-only -q` completes without duplicate `pytest_bdd` registration; see `logs/pytest_collect_only_20251006T190420Z.log` for the full transcript (warnings highlight legacy suites missing speed markers).
- 2025-10-06: Relocated stray `pytestmark` assignments below import blocks and confirmed `poetry run pytest -k nothing --collect-only` collects without SyntaxError/NameError; transcript archived at `logs/pytest_collect_only_20251006T043523Z.log`.【F:tests/integration/general/test_error_handling_at_integration_points.py†L7-L45】【F:tests/unit/application/memory/test_chromadb_store.py†L1-L58】【F:tests/behavior/steps/test_webui_integration_steps.py†L1-L58】【F:logs/pytest_collect_only_20251006T043523Z.log†L1-L113】
- 2025-10-06 23:05 UTC: Targeted behavior step collection and the neutral `-k nothing` collector finish without errors; fresh transcripts live under `diagnostics/testing/devsynth_collect_behavior_steps_20251006T230221Z.log` and `diagnostics/testing/devsynth_collect_full_suite_20251006T230249Z.log`.【F:diagnostics/testing/devsynth_collect_behavior_steps_20251006T230221Z.log†L1-L14】【F:diagnostics/testing/devsynth_collect_full_suite_20251006T230249Z.log†L1-L11】

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
