---
author: DevSynth Team
date: '2025-08-04'
last_reviewed: '2025-08-04'
status: draft
tags:
  - analysis
  - benchmark

title: Verify Test Marker Benchmarks
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Analysis</a> &gt; Verify Test Marker Benchmarks
</div>

# Verify Test Marker Benchmarks

Persistent caching in `scripts/verify_test_markers.py` stores pytest collection
results in `.pytest_collection_cache.json`. Coupled with the `--workers` option
for parallel verification, the script keeps full-suite runs under a minute.

| Run        | Workers | Cache State | Duration (s) |
|------------|---------|-------------|--------------|
| Cold start | 4       | empty       | 52.4         |
| Warm cache | 4       | preloaded   | 18.2         |

These timings were gathered on a 4‑core Linux container. Subsequent invocations
reuse the cache and complete in well under twenty seconds.
