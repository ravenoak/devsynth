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
Next Actions:
  - [ ] Refactor `src/devsynth/memory/sync_manager.py`, `src/devsynth/domain/interfaces/memory.py`, and related adapters so Protocol definitions use proper `TypeVar` parameters under Python 3.12.
  - [ ] Restore the missing `_ProgressIndicatorBase` symbol (or adjust imports) so CLI progress tests import cleanly.
  - [ ] Harden backend gating fixtures to skip providers like `kuzu` when `ModuleSpec` metadata is incomplete.
  - [ ] Re-run `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` and archive the resulting coverage bundle once collection succeeds.
Resolution Evidence:
  -
