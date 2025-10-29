---
author: DevSynth Team
date: "2025-08-25"
status: guide
version: "0.1.0a1"
---
# Smoke Benchmarks

Quick micro-benchmarks to detect gross performance regressions, aligned with project guidelines and docs/plan.md.

## Running

poetry run python scripts/smoke_bench.py

Output is JSON with min/p50/p90/max for a handful of small operations (env parsing, serialization, CLI import/parse). Use this as a local guardrail; for reproducible CI, integrate later if needed.

## Notes
- Minimal dependencies; works with --extras minimal.
- Does not access network or file system beyond standard imports.
