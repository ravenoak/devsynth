#!/usr/bin/env bash
set -euo pipefail

# Run a fast, smoke, no-parallel subset and record failures list.
# Usage: scripts/diagnostics/run_fast_smoke_baseline.sh [OUTPUT_DIR]
# Default output dir: test_reports/baselines

OUT_DIR=${1:-test_reports/baselines}
mkdir -p "$OUT_DIR"
STAMP=$(date +"%Y%m%d-%H%M%S")
OUT_FILE="$OUT_DIR/fast_smoke_baseline_${STAMP}.txt"

# Ensure Poetry is available and project deps are installed for targeted baseline
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry not found. Please install Poetry." >&2
  exit 1
fi

# Execute baseline. --maxfail=1 for quick signal; remove if you want full list.
# Users may re-run without --maxfail for comprehensive failure inventory.
CMD=(poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1)
{
  echo "Running: ${CMD[*]}";
  "${CMD[@]}" 2>&1 | tee "$OUT_FILE";
} || true

echo "Baseline output written to: $OUT_FILE"
