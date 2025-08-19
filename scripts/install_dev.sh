#!/usr/bin/env bash
set -euo pipefail

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/devsynth"
WHEEL_DIR="$CACHE_DIR/wheels"
mkdir -p "$WHEEL_DIR"

# Ensure go-task is available for Taskfile-based workflows
if ! command -v task >/dev/null 2>&1; then
  echo "[info] installing go-task"
  TASK_BIN_DIR="${HOME}/.local/bin"
  mkdir -p "$TASK_BIN_DIR"
  curl -sSL https://taskfile.dev/install.sh | bash -s -- -b "$TASK_BIN_DIR" >/tmp/task_install.log
  export PATH="$TASK_BIN_DIR:$PATH"
fi

optional_pkgs=$(poetry run python - <<'PY'
import re, tomllib

heavy = {"torch", "transformers"}
heavy_prefixes = ("nvidia-",)

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

pkgs = set()
for deps in data.get("tool", {}).get("poetry", {}).get("extras", {}).values():
    for dep in deps:
        pkg = re.split(r"[\s\[<>=]", dep, 1)[0]
        if pkg in heavy or any(pkg.startswith(p) for p in heavy_prefixes):
            continue
        pkgs.add(pkg)

print(" ".join(sorted(pkgs)))
PY
)

if [[ "${PIP_NO_INDEX:-0}" != "1" && -n "$optional_pkgs" ]]; then
  poetry run pip wheel $optional_pkgs -w "$WHEEL_DIR" >/dev/null || \
    echo "[warning] failed to cache optional extras" >&2
fi

export PIP_FIND_LINKS="$WHEEL_DIR"

# Install DevSynth with development and documentation dependencies and required extras
poetry install --with dev,docs --extras "tests retrieval chromadb api"

# Install pre-commit hooks to enable repository checks
poetry run pre-commit install --install-hooks

# Verify dependencies offline
PIP_NO_INDEX=1 poetry run pip check

# Run repository verification commands
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p benchmark"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=0
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
