---
author: DevSynth Team
date: "2025-08-25"
status: guide
version: "0.1.0a1"
---
# Memory Backend Benchmarking and Recommendations

This guide describes how to run lightweight read/write benchmarks for optional memory backends and provides practical defaults. It aligns with project guidelines and docs/plan.md (determinism, minimal deps).

## How to Run

Run the local benchmark script with environment flags indicating available backends:

- TinyDB: export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
- DuckDB: export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true
- LMDB: export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true

Then execute:

poetry run python scripts/bench_memory_backends.py

The script prints a JSON report with per-size write/read timings for ~1 KiB, 100 KiB, and 1 MiB payloads. Backends not installed or with flags unset are skipped.

## Recommendations (Default Heuristics)
- TinyDB: Prefer for small, infrequent writes and simple metadata (≤100 KiB payloads) when simplicity is paramount.
- LMDB: Solid all-around choice for key-value workloads up to a few MiB with low latency and good durability.
- DuckDB: Prefer for larger payloads and when you benefit from SQL analytics or batch operations; good for ≥1 MiB blobs and structured queries.

These are heuristics; always validate with your workload using the script above.

## Notes
- Benchmarks use temp directories and avoid network access, consistent with our test isolation principles.
- Resource flags mirror the test resource-gating system documented in project guidelines.
