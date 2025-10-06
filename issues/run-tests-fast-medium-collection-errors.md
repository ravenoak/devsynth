Title: run-tests fast+medium profile fails during collection on Python 3.12
Date: 2025-10-04 06:16 UTC
Status: open
Affected Area: tests
Reproduction:
  - `DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS=1200 poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report`
  - `DEVSYNTH_TEST_COLLECTION_TIMEOUT_SECONDS=1200 poetry run python -m pytest tests/unit --collect-only -q -o addopts= -m "fast and not memory_intensive"`
Exit Code: 1
Artifacts:
  - logs/devsynth_run_tests_fast_medium_20251004T060941Z.log
  - diagnostics/pytest_collect_unit_fast_20251004T061503Z.log
Suspected Cause: Test collection now crashes across several modules under Python 3.12. `typing.Protocol` definitions such as `MemoryStore` and `_VectorStore` are parameterized with concrete types instead of type variables, triggering `TypeError: Parameters to Protocol[...] must all be type variables`. The progress indicator helpers also reference `_ProgressIndicatorBase` before definition, and the retrieval smoke test attempts to import `kuzu`, whose distribution exposes `__spec__ = None`, raising a `ValueError` during marker evaluation. Because collection aborts early, coverage artifacts and manifests are never generated.

2025-10-06 21:30 UTC update: After reinstating optional extras, `poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel` still halts with the collection failure banner before coverage instrumentation runs; see `logs/devsynth_run-tests_fast_medium_20251006T212716Z.log`. The `test_reports/coverage_manifest_latest.json` pointer remains on the 2025-10-05 56.67 % sweep because no new artifacts were produced.【F:logs/devsynth_run-tests_fast_medium_20251006T212716Z.log†L1-L3】【F:test_reports/coverage_manifest_latest.json†L1-L24】
2025-10-06 21:46 UTC update: Manual CLI reruns now hang during pytest collection even before the failure banner appears. `logs/devsynth_run-tests_fast_medium_20251127T002200Z.log` captures an empty transcript, and the companion diagnostics summary documents the active collector process (`/workspace/devsynth/.venv/bin/python -m pytest tests/ --collect-only -q -o addopts=`) consuming CPU until interrupted. No coverage artifacts or knowledge-graph banners were produced.【F:diagnostics/testing/devsynth_run_tests_fast_medium_20251127T002200Z_summary.txt†L1-L11】
Next Actions:
  - [ ] Refactor `src/devsynth/memory/sync_manager.py`, `src/devsynth/domain/interfaces/memory.py`, and related adapters so Protocol definitions use proper `TypeVar` parameters under Python 3.12.
  - [ ] Restore the missing `_ProgressIndicatorBase` symbol (or adjust imports) so CLI progress tests import cleanly.
  - [ ] Harden backend gating fixtures to skip providers like `kuzu` when `ModuleSpec` metadata is incomplete.
  - [ ] Re-run `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` and archive the resulting coverage bundle once collection succeeds.
Resolution Evidence:
  -
