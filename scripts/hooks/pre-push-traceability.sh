#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

poetry run pytest
poetry run python scripts/update_traceability.py
