---
author: DevSynth Team
date: "2025-08-26"
status: active
version: "0.1.0a1"
---
# Performance Tests Policy (tests/performance/)

This policy defines how performance/benchmark tests are organized, executed, and gated in the DevSynth repository. It aligns with project guidelines and the stabilization plan in docs/plan.md.

## Scope and location
- Performance and benchmarks live under `tests/performance/`.
- They validate throughput/latency characteristics and detect regressions but are not required for functional correctness of PRs.

## Opt-in by default
- Performance tests are opt-in and excluded from default PR runs.
- Mark all such tests with `@pytest.mark.performance` in addition to an appropriate speed marker (`@pytest.mark.slow` is typical due to workload size).
- Examples:
  - Module-level:
    ```python
    import pytest
    pytestmark = [pytest.mark.performance]
    ```
  - Per-test:
    ```python
    @pytest.mark.performance
    @pytest.mark.slow
    def test_throughput(...):
        ...
    ```

## How to run locally
- By marker selection:
  - poetry run pytest -m performance tests/performance/
- Benchmarks using pytest-benchmark (where applicable):
  - DEVSYNTH_ENABLE_BENCHMARKS=true poetry run pytest -p benchmark -m performance tests/performance/
- You can combine with `-k` to filter specific files/tests.

## Resource gating and isolation
- Benchmarks may require the `pytest-benchmark` plugin; tests should be skipped automatically if the plugin is not active.
- Some tests gate on environment variables for safety, for example:
  - `DEVSYNTH_ENABLE_BENCHMARKS=true` to allow heavier benchmarks to run.
- All performance tests must:
  - Avoid network access (use stubs; rely on the `disable_network` fixture) unless explicitly guarded by `@pytest.mark.requires_resource("<name>")`.
  - Be deterministic when feasible (seeded RNG, fixed workloads).
  - Write only under tmp paths or designated docs/performance metrics files in CI-approved flows.

## CI policy
- Default PR jobs do NOT run `-m performance`.
- Nightly or manual jobs MAY run performance suites and publish artifacts (e.g., JSON metrics) under `docs/performance/` or `test_reports/`.
- Stability notes:
  - Keep workloads sized to complete under reasonable time limits when run locally.
  - Document any variability and provide guidance for interpreting trends.

## References
- project guidelines (Testing discipline; determinism)
- docs/plan.md (Stabilization priorities)
- docs/performance/performance_and_scalability_testing.md (How-to guides)
