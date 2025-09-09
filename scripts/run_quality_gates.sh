#!/usr/bin/env bash
# scripts/run_quality_gates.sh — Consolidated quality gates runner for docs/tasks.md Tasks 49–56
#
# Usage:
#   bash scripts/run_quality_gates.sh
#
# Behavior:
# - Ensures test_reports/quality/ exists
# - Runs formatting and lint/typing/security checks via Poetry
# - Captures outputs to:
#     test_reports/quality/black_report.txt
#     test_reports/quality/isort_report.txt
#     test_reports/quality/flake8_report.txt
#     test_reports/quality/mypy_report.txt
#     test_reports/quality/bandit_report.txt
#     test_reports/quality/safety_report.txt
# - For black/isort, tries --check then auto-fixes if needed and appends outputs
# - Exits non-zero if any gating tool (flake8/mypy/bandit/safety) fails
#
# Notes:
# - This script does not change repo state except when auto-fixing format with black/isort.
# - Prefer to run under a Poetry-managed environment to ensure consistent plugin availability.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
QUALITY_DIR="${ROOT_DIR}/test_reports/quality"
mkdir -p "${QUALITY_DIR}"

# Ensure poetry is present
if ! command -v poetry >/dev/null 2>&1; then
  echo "Poetry is required but not found in PATH." >&2
  exit 127
fi

# Helper to run a command and capture output to a file, preserving exit code
run_and_tee() {
  local outfile="$1"; shift
  set +e
  "$@" | tee "${outfile}"
  local rc=$?
  set -e
  return $rc
}

# 49. Black check (auto-fix if needed)
BLACK_OUT="${QUALITY_DIR}/black_report.txt"
echo "[quality] Running black --check ." | tee "${BLACK_OUT}"
set +e
poetry run black . --check | tee -a "${BLACK_OUT}"
BLACK_RC=${PIPESTATUS[0]}
set -e
if [ ${BLACK_RC} -ne 0 ]; then
  echo "[quality] black --check failed; auto-formatting with black ." | tee -a "${BLACK_OUT}"
  poetry run black . | tee -a "${BLACK_OUT}"
fi

# 50. isort check (auto-fix if needed)
ISORT_OUT="${QUALITY_DIR}/isort_report.txt"
echo "[quality] Running isort --check-only ." | tee "${ISORT_OUT}"
set +e
poetry run isort . --check-only | tee -a "${ISORT_OUT}"
ISORT_RC=${PIPESTATUS[0]}
set -e
if [ ${ISORT_RC} -ne 0 ]; then
  echo "[quality] isort --check-only failed; applying isort ." | tee -a "${ISORT_OUT}"
  poetry run isort . | tee -a "${ISORT_OUT}"
fi

# 51. flake8
FLAKE8_OUT="${QUALITY_DIR}/flake8_report.txt"
echo "[quality] Running flake8 src/ tests/" | tee "${FLAKE8_OUT}"
run_and_tee "${FLAKE8_OUT}" poetry run flake8 src/ tests/

# 52. mypy strict
MYPY_OUT="${QUALITY_DIR}/mypy_report.txt"
echo "[quality] Running mypy src/devsynth (strict mode per pyproject)" | tee "${MYPY_OUT}"
run_and_tee "${MYPY_OUT}" poetry run mypy src/devsynth

# 54. bandit (exclude tests)
BANDIT_OUT="${QUALITY_DIR}/bandit_report.txt"
echo "[quality] Running bandit -r src/devsynth -x tests" | tee "${BANDIT_OUT}"
run_and_tee "${BANDIT_OUT}" poetry run bandit -r src/devsynth -x tests

# 55. safety full report
SAFETY_OUT="${QUALITY_DIR}/safety_report.txt"
echo "[quality] Running safety check --full-report" | tee "${SAFETY_OUT}"
run_and_tee "${SAFETY_OUT}" poetry run safety check --full-report

echo "[quality] Completed. Reports under ${QUALITY_DIR}"
