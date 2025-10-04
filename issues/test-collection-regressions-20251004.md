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

## Next Actions
- [ ] Restore `_ProgressIndicatorBase` exports (likely `devsynth.application.cli.long_running_progress`) and ensure tests import helpers from supported modules.
- [x] Rework `MemoryStore` and related Protocol definitions to use proper `TypeVar` generics; add unit tests to prove runtime + mypy compatibility.
- [ ] Move `pytest_plugins` declarations into the repository root `conftest.py` or convert to plugin registration helpers.
- [ ] Recreate or relocate the missing `.feature` files referenced by behavior suites; update loaders and traceability documents accordingly.
- [ ] Guard optional backend tests with `pytest.importorskip` plus `requires_resource` flags so they skip cleanly without extras.
- [ ] Re-run smoke and `--collect-only` commands, attaching new logs when failures cease.

## Resolution Evidence
- 2025-10-04: Smoke command still fails pending broader regression fixes; captured output in `logs/devsynth_run-tests_smoke_fast_20251004T201351Z.log`.
