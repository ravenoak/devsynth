---
title: "`devsynth run-tests` Workflow Analysis"
date: "2025-08-23"
version: "0.1.0-alpha.1"
tags:
  - devsynth
  - testing
  - analysis
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-23"
---

# `devsynth run-tests` Workflow

This document describes the test-runner workflow exposed by `devsynth run-tests`. It focuses on the arguments that control termination and discusses the asymptotic cost of different execution modes. Benchmark runs on the DevSynth CI container illustrate expected runtime.

## Workflow Overview

1. **Collection** – test files are selected based on the `--target` and `--speed` filters.
2. **Execution** – tests run in parallel by default using `pytest-xdist` workers.
3. **Reporting** – optional `--report` generates HTML coverage under `test_reports/`.
4. **Termination guards** – optional provider checks and failure limits prevent hangs:
   - Missing optional dependencies set `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE=false` so the suite skips the associated tests instead of waiting indefinitely.
   - `--maxfail <n>` stops the run after `n` failures.
   - `--segment` with `--segment-size` executes the suite in batches, allowing early termination between segments.

## Complexity Estimates

Let `N` be the number of collected tests and `P` the number of workers.

| Mode | Complexity | Notes |
|------|------------|-------|
| Parallel (default) | `O(N / P)` | Workers execute tests concurrently. |
| `--no-parallel` | `O(N)` | Runs tests serially; coverage checks can dominate runtime. |
| `--segment` with size `s` | `O(N / P + N/s)` | Adds overhead for each segment; useful for isolating failures. |
| `--maxfail = m` | `O(min(m, N) / P)` | Terminates after first `m` failures. |

The optional dependency guard yields constant-time termination when required services are absent.

## Benchmark Results

The table below summarizes wall-clock runtimes observed on the CI container (5 vCPUs, Python 3.12) when running the fast test suite.

| Configuration | Real Time | Notes |
|---------------|-----------|-------|
| Default (`--speed=fast`) | 45.6 s | 150 passed, 25 skipped. |
| `--no-parallel` | 107.2 s | Coverage check failed at 20% (149 passed, 25 skipped). |
| `--segment --segment-size=10` | 161.3 s | Executed in 14 batches, 150 passed. |

## Termination Arguments

- `--maxfail <n>` limits failures before exit.
- `--segment`/`--segment-size` allow controlled batching.
- Optional provider environment variables (e.g., `DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE=false`) skip tests that would otherwise stall.

These mechanisms ensure `devsynth run-tests` terminates even when external services are missing or failures occur early in the suite.
