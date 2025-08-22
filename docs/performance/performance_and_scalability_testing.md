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

## Interpreting results

Each metrics file stores:

- `workload`: number of operations executed
- `duration_seconds`: elapsed wall-clock time
- `throughput_ops_per_s`: operations per second

Higher throughput indicates better performance. Compare metrics across commits to detect regressions or scalability issues.
