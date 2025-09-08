#!/usr/bin/env bash
set -euo pipefail
# Iteration validation script: collection, smoke, fast+medium with report, coverage combine
# This script is idempotent and safe to run multiple times. It respects existing environment overrides.

echo "[iteration] collection only"
poetry run pytest --collect-only -q || true

mkdir -p test_reports htmlcov diagnostics

echo "[iteration] smoke fast no-parallel"
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 2>&1 | tee test_reports/smoke_fast.log || true

echo "[iteration] full fast+medium with report, no-parallel"
poetry run devsynth run-tests --speed=fast --speed=medium --report --no-parallel 2>&1 | tee test_reports/full_fast_medium.log || true

# Combine coverage artifacts written by pytest-cov across runs
if command -v poetry >/dev/null 2>&1; then
  echo "[iteration] coverage combine + html + json"
  poetry run coverage combine || true
  poetry run coverage html -d htmlcov || true
  poetry run coverage json -o coverage.json || true
fi

echo "[iteration] done; artifacts under test_reports/ and htmlcov/, coverage.json present"
