---
author: DevSynth Team
date: "2025-08-26"
status: reference
version: "0.1.0a1"
---
# Fast Smoke Baseline

Purpose: Establish and record a baseline of failures for the fast+smoke+no-parallel subset to surface deterministic issues quickly. Aligns with docs/tasks.md item 1.

How to run:

```bash
# Ensure development dependencies are installed
poetry install --with dev --extras "tests retrieval chromadb api"

# Run baseline and capture output under test_reports/baselines/
bash scripts/diagnostics/run_fast_smoke_baseline.sh
```

Notes:
- The script runs with --maxfail=1 for quick signal. Re-run without --maxfail to capture the full failure inventory once initial issues are addressed.
- Attach the produced file to PRs when triaging failures.
- Prefer running from a clean working tree. Use devsynth doctor for quick sanity.
