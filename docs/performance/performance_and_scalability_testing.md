# Performance and Scalability Testing

DevSynth captures repeatable benchmarks for core operations. This guide explains how to run the benchmarks and interpret their results.

## Running the benchmarks

Use the `pytest-benchmark` plugin to execute the baseline and scalability tests:

```bash
poetry run pytest tests/performance/test_performance_metrics.py
```

To generate metrics files directly:

```bash
poetry run python - <<'PY'
from pathlib import Path
from devsynth.testing.performance import (
    capture_baseline_metrics,
    capture_scalability_metrics,
)

capture_baseline_metrics(100000, output_path=Path("docs/performance/baseline_metrics.json"))
capture_scalability_metrics(
    [10000, 100000, 1000000],
    output_path=Path("docs/performance/scalability_metrics.json"),
)
PY
```

## Performance Tests Policy

Performance tests and benchmarks are opt-in by default and must not run in the standard fast path or CI smoke jobs.

- Mark all performance or benchmark tests with `@pytest.mark.performance`.
- Do not include performance tests in the default fast runs executed by `devsynth run-tests --speed=fast`.
- Avoid flakiness by:
  - Disabling external network and services during perf runs unless explicitly needed.
  - Using fixed seeds and controlled environments.
  - Increasing warmup iterations and repeating measurements to smooth variance.
- Provide a clear local run command and keep CI jobs for performance optional or nightly only.

### Running performance tests locally

```bash
# Run only performance tests
poetry run pytest -m performance tests/performance/

# Or use the devsynth runner with slow markers enabled
poetry run devsynth run-tests --speed=slow
```

Ensure your environment is quiet (no heavy background tasks) and pin CPU scaling if possible.

### CI Guidance

- Performance tests are skipped in default CI runs. Configure a separate, non-blocking workflow if you need perf tracking.
- Publish benchmark output as artifacts when enabled; do not fail PRs on perf regressions unless the threshold and methodology are agreed upon.

## Interpreting results

Each metrics file stores:

- `workload`: number of operations executed
- `duration_seconds`: elapsed wall-clock time
- `throughput_ops_per_s`: operations per second

Higher throughput indicates better performance. Compare metrics across commits to detect regressions or scalability issues.
