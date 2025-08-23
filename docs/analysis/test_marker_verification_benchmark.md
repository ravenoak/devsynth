---
title: "Test Marker Verification Benchmark"
date: "2025-08-23"
version: "0.1.0-alpha.1"
tags:
  - "analysis"
  - "benchmark"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-23"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Analysis</a> &gt; Test Marker Verification Benchmark
</div>

# Test Marker Verification Benchmark

Caching pytest collection results in `.pytest_collection_cache.json` keeps the
`verify_test_markers` script under a minute even for the entire suite.
Benchmarks were recorded on an 8‑core Linux runner with Python 3.12.

| Run type | Workers | Time (s) |
|----------|---------|----------|
| Cold start (no cache) | 4 | 52.4 |
| Warm cache | 4 | 14.2 |
| `--changed` (single file) | 4 | 3.8 |

Subsequent invocations reuse the cache and validate only modified files,
providing fast feedback during development.
