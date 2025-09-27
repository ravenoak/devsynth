#!/usr/bin/env bash
set -euo pipefail

mkdir -p test_reports

export DEVSYNTH_WEBUI_COVERAGE=1

poetry run coverage erase

poetry run coverage run -m pytest \
  tests/unit/interface/test_webui_bridge_*.py \
  tests/unit/interface/test_webui_display_and_layout.py \
  tests/unit/interface/test_webui_progress.py \
  | tee test_reports/webui_interface_coverage.txt

poetry run coverage run -a scripts/exercise_webui_interface.py

poetry run coverage report \
  --include="*/webui_bridge.py,*/webui.py" \
  --show-missing \
  --fail-under=0 \
  >> test_reports/webui_interface_coverage.txt
