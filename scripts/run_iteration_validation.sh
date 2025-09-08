#!/usr/bin/env bash
set -euo pipefail
# Smoke validations per guidelines
export PYTEST_ADDOPTS=""
poetry run pytest --collect-only -q || true
poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1 || true
poetry run python scripts/coverage_summary.py || true
