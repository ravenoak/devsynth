#!/usr/bin/env bash
set -euo pipefail

# scripts/collect_smoke_timing.sh
# Measures the duration of the smoke fast test lane and writes the artifact
# to test_reports/smoke_fast_timing.txt. Intended for local use; CI has an
# integrated measurement as well.
#
# Usage:
#   scripts/collect_smoke_timing.sh [--] [extra pytest args...]
# Example:
#   scripts/collect_smoke_timing.sh -- -k "not slow"  # forwards args after -- to devsynth run-tests
#
# Behavior:
# - Ensures test_reports/ exists.
# - Sets PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 to mirror smoke mode.
# - Invokes: poetry run devsynth run-tests --smoke --speed=fast --no-parallel "$@"
# - Writes elapsed seconds as a single line to test_reports/smoke_fast_timing.txt

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPORT_DIR="$ROOT_DIR/test_reports"
TIMING_FILE="$REPORT_DIR/smoke_fast_timing.txt"

mkdir -p "$REPORT_DIR"

start_ts=$(date +%s)
# Ensure smoke behavior regardless of ambient environment
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export DEVSYNTH_OFFLINE=${DEVSYNTH_OFFLINE:-true}
export DEVSYNTH_PROVIDER=${DEVSYNTH_PROVIDER:-stub}

# Run the smoke fast lane via CLI wrapper
poetry run devsynth run-tests --smoke --speed=fast --no-parallel "$@" || true

end_ts=$(date +%s)
elapsed=$(( end_ts - start_ts ))

printf "%s\n" "$elapsed" > "$TIMING_FILE"

printf "Smoke fast lane duration: %ss (written to %s)\n" "$elapsed" "$TIMING_FILE"
