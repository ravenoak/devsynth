---
author: DevSynth Team
date: '2025-08-23'
last_reviewed: '2025-08-23'
status: draft
tags:
  - analysis
  - testing
  - benchmarks
title: "devsynth run-tests Workflow"
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Analysis</a> &gt; devsynth run-tests Workflow
</div>

# devsynth `run-tests` Workflow

This analysis specifies how the `devsynth run-tests` CLI orchestrates the test
suite, termination guarantees, and expected runtime.

## Workflow Overview

1. **Option parsing** – CLI arguments (`--target`, `--speed`, `--report`,
   `--maxfail`, etc.) are validated and mapped to `pytest` parameters.
2. **Optional provider gating** – missing optional dependencies (e.g. LM
   Studio) set `DEVSYNTH_RESOURCE_*` flags to avoid hangs.
3. **Execution** – `pytest` is invoked directly or via `xdist` for parallel
   execution. Segmentation (`--segment`/`--segment-size`) batches the test list
   to control memory usage.
4. **Reporting** – results stream through the selected UX bridge. When `--report`
   is set, an HTML report is written under `test_reports/`.

## Termination Arguments

- The test set is finite; without segmentation the run finishes after each test
  executes once.
- With segmentation, each segment processes a disjoint subset of tests. The
  loop terminates after `ceil(n/segment_size)` iterations.
- `--maxfail` instructs `pytest` to abort after *k* failures, guaranteeing exit
  even when failures would otherwise cascade.
- Optional provider flags force-skipping unavailable integrations, preventing
  hangs on external services.

## Complexity Estimates

Let *n* be the number of collected tests and *p* the number of workers when
running in parallel.

- **Sequential**: `O(n)`
- **Parallel**: `O(n/p)` work plus `O(p)` coordination overhead
- **Segmented**: `O(n)` overall with `O(segment_size)` memory per batch
- **Early exit**: `O(min(n, k))` when `--maxfail=k`

## Benchmark Results

| Configuration | Command | Runtime (real) | Notes |
|---------------|---------|---------------|-------|
| Sequential | `devsynth run-tests --target unit-tests --speed=fast --no-parallel` | 66.3s | full suite, 1 failure |
| Parallel | `devsynth run-tests --target unit-tests --speed=fast` | 31.1s | full suite, 1 failure |
| Early exit | `devsynth run-tests --target unit-tests --speed=fast --maxfail=1` | 28.8s | stopped after first failure |

Runtimes were captured with `time` on a 4‑vCPU container. The failing test
(`test_speed_option_recognized`) demonstrates the early‐exit behaviour.

## Conclusion

`devsynth run-tests` completes once all selected tests run or the `--maxfail`
threshold is reached. Complexity scales linearly with the number of tests, and
parallel execution divides work across workers with modest coordination cost.
