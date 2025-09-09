#!/usr/bin/env bash
# scripts/run_marker_discipline.sh — runs marker verification and emits standardized artifacts
# Usage:
#   bash scripts/run_marker_discipline.sh
# Behavior:
# - Ensures test_reports/ exists
# - Runs verify_test_markers.py to produce test_reports/test_markers_report.json
# - Runs verify_test_markers.py --changed (best-effort; does not fail script if no changes)
# - Exits non-zero if the full report run finds violations
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
REPORT_DIR="${ROOT_DIR}/test_reports"
mkdir -p "${REPORT_DIR}"

# Ensure poetry is present
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry is required but not found in PATH." >&2
  exit 127
fi

REPORT_FILE="${REPORT_DIR}/test_markers_report.json"

echo "[run_marker_discipline] Generating full marker report -> ${REPORT_FILE}"
poetry run python scripts/verify_test_markers.py --report --report-file "${REPORT_FILE}"

# Run changed-only check (best-effort)
echo "[run_marker_discipline] Running changed-only verification (best effort)"
set +e
poetry run python scripts/verify_test_markers.py --changed
CHANGED_RC=$?
set -e
if [ "$CHANGED_RC" -ne 0 ]; then
  echo "[run_marker_discipline] --changed reported issues (this does not override the full report result)." >&2
fi

echo "[run_marker_discipline] Completed. Report at ${REPORT_FILE}"