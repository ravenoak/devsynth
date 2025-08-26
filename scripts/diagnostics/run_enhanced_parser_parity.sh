#!/usr/bin/env bash
set -euo pipefail

# Run the enhanced test parser parity check against the tests/ directory
# and write a JSON report under test_reports/ for later inspection.
# Aligns with .junie/guidelines.md (run via Poetry) and docs/plan.md (determinism, diagnostics).

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

REPORT_DIR="test_reports"
REPORT_FILE="$REPORT_DIR/enhanced_parser_parity.json"

mkdir -p "$REPORT_DIR"

# Use Poetry to ensure plugins and env are consistent
if command -v poetry >/dev/null 2>&1; then
  poetry run python scripts/enhanced_test_parser.py --directory tests --compare --report --report-file "$REPORT_FILE"
else
  echo "Warning: poetry not found; falling back to system python"
  python scripts/enhanced_test_parser.py --directory tests --compare --report --report-file "$REPORT_FILE"
fi

echo "Enhanced parser parity report generated at: $REPORT_FILE"
