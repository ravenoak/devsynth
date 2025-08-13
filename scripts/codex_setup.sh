#!/usr/bin/env bash
set -exo pipefail

# NOTE: This script provisions the Codex testing environment only. It is not
# intended for regular development setup.

# Ensure pipx is available for installing the CLI. When rerunning offline,
# skip installation if pipx is already present so the script can proceed
# without network access.
if ! command -v pipx >/dev/null; then
  if command -v apt-get >/dev/null; then
    for _ in 1 2 3; do
      if apt-get update && apt-get install -y pipx; then
        break
      else
        sleep 5
      fi
    done
    if ! command -v pipx >/dev/null; then
      echo "[warning] failed to install pipx with apt-get" >&2
      python3 -m pip install --user pipx || \
        echo "[warning] pip install pipx failed" >&2
    fi
  else
    echo "[warning] apt-get unavailable; attempting pip install of pipx" >&2
    python3 -m pip install --user pipx || \
      echo "[warning] pip install pipx failed" >&2
  fi
fi
export PATH="$HOME/.local/bin:$PATH"
pipx ensurepath

# Run commands and exit with a clear message on failure
run_check() {
  local desc="$1"
  shift
  if ! "$@"; then
    echo "$desc failed" >&2
    exit 1
  fi
}

# Use Python 3.12 if available, otherwise fall back to Python 3.11
poetry env use "$(command -v python3.12 || command -v python3.11)"

# Verify that the virtual environment was created
poetry env info --path >/dev/null

# Dialectical checkpoints
echo "DIALECTICAL CHECKPOINT: What dependencies are truly required?"
echo "DIALECTICAL CHECKPOINT: How do we verify the cache reproduces identical environments?"

EXPECTED_VERSION="0.1.0-alpha.1"
CURRENT_VERSION="$(poetry version -s)"
if [[ "$CURRENT_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "Project version $CURRENT_VERSION does not match $EXPECTED_VERSION" >&2
  exit 1
fi

EXTRAS="tests retrieval chromadb api"
CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/devsynth"
WHEEL_DIR="$CACHE_DIR/wheels"
mkdir -p "$WHEEL_DIR"

optional_pkgs=$(poetry run python - <<'PY'
import re
import tomllib

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
poetry install \
  --with dev \
  --extras "$EXTRAS" \
  --no-interaction

# Ensure prometheus-client is available after installation
poetry run python -c "import prometheus_client"
# Handle normalized package names with underscores
poetry run pip list | grep prometheus-client >/dev/null || \
  poetry run pip list | grep prometheus_client >/dev/null

# Install the DevSynth CLI with pipx and verify it works. On subsequent
# runs, skip the installation step to avoid network access.
if command -v devsynth >/dev/null; then
  echo "[info] devsynth CLI already installed; skipping pipx install"
else
  pipx install --editable . --force
  poetry run pip freeze > /tmp/devsynth-requirements.txt
  pipx runpip devsynth install -r /tmp/devsynth-requirements.txt || \
    echo "[warning] pipx runpip devsynth failed" >&2
fi
command -v devsynth >/dev/null
devsynth --help >/dev/null || echo "[warning] devsynth --help failed"

# Validate dependency installation
poetry run pip check

# Prefetch the cl100k_base encoding for tiktoken
poetry run python - <<'EOF'
import sys
try:
    import tiktoken
    tiktoken.get_encoding("cl100k_base")
except Exception as exc:
    print(f"[warning] failed to prefetch tiktoken encoding: {exc}", file=sys.stderr)
    sys.exit(1)
EOF

# Verify key packages (including test extras) are present
poetry run python - <<'EOF'
import importlib
import sys

required = [
    "pytest",
    "pytest_bdd",
    "pydantic",
    "yaml",
    "typer",
    "tiktoken",
    "fastapi",
    "streamlit",
    "tinydb",
    "duckdb",
    "lmdb",
    "astor",
    "httpx",
    "prometheus_client",
    "chromadb",
    "numpy",
]
optional = [
    "kuzu",
    "faiss",
    "dearpygui",
    "lmstudio",
]

missing = []
for pkg in required:
    try:
        importlib.import_module(pkg)
    except Exception:
        missing.append(pkg)

optional_missing = []
for pkg in optional:
    try:
        importlib.import_module(pkg)
    except Exception:
        optional_missing.append(pkg)

if missing:
    sys.exit("Missing packages: " + ", ".join(missing))

for pkg in optional_missing:
    print(f"[warning] optional package {pkg} is not installed", file=sys.stderr)
EOF

# Ensure dependency tree is healthy after installing extras
poetry run pip check

# Kuzu is optional; skip related tests if it's not installed
if ! poetry run python -c "import kuzu" >/dev/null 2>&1; then
  echo "[warning] kuzu package not installed; kuzu tests will be skipped"
  export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=false
else
  export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
fi

# Run a smoke test to catch failures early
poetry run pytest tests/behavior/steps/test_alignment_metrics_steps.py --maxfail=1

# Use the CLI to run a fast, non-interactive test sweep. The timeout prevents
# hangs while the log aids in diagnosing failures.
# What evidence shows the CLI can run tests non-interactively?
timeout 15m poetry run devsynth run-tests --speed=fast | tee devsynth_cli_tests.log

# Run the dialectical audit and surface any unanswered questions.
poetry run python scripts/dialectical_audit.py || true
if [ -f dialectical_audit.log ]; then
  poetry run python - <<'PY'
import json
from pathlib import Path

data = json.loads(Path('dialectical_audit.log').read_text())
questions = data.get('questions', [])
if questions:
    print('Unanswered Socratic questions:')
    for q in questions:
        print(f'- {q}')
PY
fi

run_check "Test organization verification" poetry run python tests/verify_test_organization.py
run_check "Test marker verification" poetry run python scripts/verify_test_markers.py
run_check "Requirements traceability verification" poetry run python scripts/verify_requirements_traceability.py
run_check "Version synchronization verification" poetry run python scripts/verify_version_sync.py

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED
