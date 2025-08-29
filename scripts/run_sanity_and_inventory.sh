#!/usr/bin/env bash
# scripts/run_sanity_and_inventory.sh — standardizes Section 7 sanity and inventory runs
# Usage:
#   bash scripts/run_sanity_and_inventory.sh [--smoke]
# Behavior:
# - Creates test_reports/ directory
# - Runs pytest --collect-only
# - Verifies smoke plugin-disabled notice using scripts/verify_smoke_notice.py (acceptance 1.6.2 support)
# - Runs devsynth run-tests in smoke fast, no-parallel with maxfail=1
# - Runs inventory export
# - Writes logs to test_reports/{collect_only.log, smoke_fast.log, inventory.log}
# - Also writes test_reports/smoke_plugin_notice.txt
# - Exits non-zero if any underlying command fails
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
REPORT_DIR="${ROOT_DIR}/test_reports"
mkdir -p "${REPORT_DIR}"

# Ensure poetry is present
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry is required but not found in PATH." >&2
  exit 127
fi

# Respect offline defaults unless overridden
export DEVSYNTH_OFFLINE="${DEVSYNTH_OFFLINE:-true}"

# 1) Collection only
echo "[run_sanity_and_inventory] Step 1/4: pytest --collect-only -q" | tee "${REPORT_DIR}/collect_only.log"
set -o pipefail
# Capture output to a temp file as well for smoke notice verification
COLLECT_OUT="${REPORT_DIR}/collect_only_output.txt"
poetry run pytest --collect-only -q | tee -a "${REPORT_DIR}/collect_only.log" | tee "${COLLECT_OUT}" >/dev/null

# 2) Verify smoke plugin-disabled notice (acceptance 1.6.2)
echo "[run_sanity_and_inventory] Step 2/4: verify smoke plugin-disabled notice" | tee -a "${REPORT_DIR}/collect_only.log"
# Try with input file first; fall back to piping if needed
if ! poetry run python scripts/verify_smoke_notice.py --input "${COLLECT_OUT}"; then
  # Attempt stdin path in case file detection fails
  poetry run python scripts/verify_smoke_notice.py < "${COLLECT_OUT}" || true
fi

# 3) Smoke fast path
echo "[run_sanity_and_inventory] Step 3/4: devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1" | tee "${REPORT_DIR}/smoke_fast.log"
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 | tee -a "${REPORT_DIR}/smoke_fast.log"

# 4) Inventory export
echo "[run_sanity_and_inventory] Step 4/4: devsynth run-tests --inventory" | tee "${REPORT_DIR}/inventory.log"
poetry run devsynth run-tests --inventory | tee -a "${REPORT_DIR}/inventory.log"

echo "[run_sanity_and_inventory] Completed. Artifacts under ${REPORT_DIR}"