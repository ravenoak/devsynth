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

  if command -v curl >/dev/null 2>&1; then
    curl -sSL https://taskfile.dev/install.sh | bash -s -- -b "$TASK_BIN_DIR" >/tmp/task_install.log
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://taskfile.dev/install.sh | bash -s -- -b "$TASK_BIN_DIR" >/tmp/task_install.log
  else
    echo "[error] neither curl nor wget is available" >&2
    exit 1
  fi

  export PATH="$TASK_BIN_DIR:$PATH"
  echo "$TASK_BIN_DIR" >> "${GITHUB_PATH:-/dev/null}" 2>/dev/null || true
fi

# Ensure the task binary is available after installation
if ! command -v task >/dev/null 2>&1; then
  echo "[error] task binary not found on PATH after installation" >&2
  exit 1
fi

# Display Task version for debugging and ensure it resolves
if ! task_version="$(task --version 2>/dev/null)"; then
  echo "[error] failed to determine task version" >&2
  exit 1
fi
if [[ -z "$task_version" ]]; then
  echo "[error] task version output empty" >&2
  exit 1
fi
echo "$task_version"

# Ensure Poetry manages a dedicated virtual environment
poetry config virtualenvs.create true
poetry env remove --all >/dev/null 2>&1 || true

optional_pkgs=$(python - <<'PY'
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

missing_pkgs=()
for pkg in $optional_pkgs; do
  if ! ls "$WHEEL_DIR"/"$pkg"-*.whl >/dev/null 2>&1; then
    missing_pkgs+=("$pkg")
  fi
done

if [[ "${PIP_NO_INDEX:-0}" != "1" && ${#missing_pkgs[@]} -gt 0 ]]; then
  if ! pip wheel "${missing_pkgs[@]}" -w "$WHEEL_DIR" >/dev/null; then
    echo "[warning] failed to cache optional extras" >&2
  fi
fi

export PIP_FIND_LINKS="$WHEEL_DIR"

# Install DevSynth with development and documentation dependencies and required extras
poetry install --with dev,docs --extras "tests retrieval chromadb api"

# Fail fast if Poetry did not create a virtual environment
if ! venv_path="$(poetry env info --path 2>/dev/null)"; then
  echo "[error] poetry virtualenv path not found" >&2
  exit 1
fi
if [[ -z "$venv_path" ]]; then
  echo "[error] poetry virtualenv path not found" >&2
  exit 1
fi
echo "[info] poetry virtualenv: $venv_path"

# Confirm the DevSynth CLI is available
if ! poetry run devsynth --help >/dev/null 2>&1; then
  echo "[error] devsynth console script not found" >&2
  exit 1
fi

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
