#!/usr/bin/env bash
set -exo pipefail

START_TIME=$(date +%s)
MAX_SECONDS=$((15 * 60))
WARN_SECONDS=$((10 * 60))

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  cd "$PROJECT_ROOT"
fi

# NOTE: This script provisions the Codex testing environment only. It is not
# intended for regular development setup. To keep the ephemeral workspace
# responsive, it targets completion in under 10 minutes and fails if it
# exceeds 15 minutes.
# See AGENTS.md for repository instructions; only AGENTS.md and this file should
# reference AGENTS guidelines or `codex_setup.sh`.

# Ensure pipx is available for installing the CLI. When rerunning offline,
# skip installation if pipx is already present so the script can proceed
# without network access.
PIPX_BIN_DIR="$HOME/.local/bin"
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
if [[ ":$PATH:" != *":$PIPX_BIN_DIR:"* ]]; then
  export PATH="$PIPX_BIN_DIR:$PATH"
fi
pipx ensurepath
if [ -w "$HOME/.profile" ] && ! grep -F "$PIPX_BIN_DIR" "$HOME/.profile" >/dev/null 2>&1; then
  echo "export PATH=\"$PIPX_BIN_DIR:\$PATH\"" >> "$HOME/.profile"
fi

# Run commands and exit with a clear message on failure
run_check() {
  local desc="$1"
  shift
  if ! "$@"; then
    echo "$desc failed" >&2
    exit 1
  fi
}

# Ensure Python 3.12 is installed and selected
if ! command -v python3.12 >/dev/null; then
  if command -v apt-get >/dev/null; then
    for _ in 1 2 3; do
      if apt-get update && apt-get install -y python3.12 python3.12-venv python3.12-dev; then
        break
      else
        sleep 5
      fi
    done
  fi
  if ! command -v python3.12 >/dev/null; then
    echo "Python 3.12 is required but could not be installed" >&2
    exit 1
  fi
fi

# Use Python 3.12
poetry env use "$(command -v python3.12)"

# Verify that the virtual environment was created
poetry env info --path >/dev/null

# Ensure go-task is available for Taskfile workflows
TASK_BIN_DIR="${HOME}/.local/bin"
mkdir -p "$TASK_BIN_DIR"
if ! command -v task >/dev/null 2>&1; then
  echo "[info] task command missing; installing go-task" >&2
  os=$(uname -s | tr '[:upper:]' '[:lower:]')
  arch=$(uname -m)
  case "$arch" in
    x86_64|amd64) arch="amd64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) echo "[error] unsupported architecture: $arch" >&2; exit 1 ;;
  esac
  case "$os" in
    linux|darwin) : ;;
    *) echo "[error] unsupported OS: $os" >&2; exit 1 ;;
  esac
  TASK_URL="https://github.com/go-task/task/releases/latest/download/task_${os}_${arch}.tar.gz"
  if command -v curl >/dev/null 2>&1; then
    curl -sSL "$TASK_URL" | tar -xz -C "$TASK_BIN_DIR" task >/tmp/task_install.log 2>&1
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$TASK_URL" | tar -xz -C "$TASK_BIN_DIR" task >/tmp/task_install.log 2>&1
  else
    echo "[error] neither curl nor wget is available" >&2
    exit 1
  fi
  export PATH="$TASK_BIN_DIR:$PATH"
fi
if [[ ":$PATH:" != *":$TASK_BIN_DIR:"* ]]; then
  export PATH="$TASK_BIN_DIR:$PATH"
fi
if [ -w "$HOME/.profile" ] && ! grep -F "$TASK_BIN_DIR" "$HOME/.profile" >/dev/null 2>&1; then
  echo "export PATH=\"$TASK_BIN_DIR:\$PATH\"" >> "$HOME/.profile"
fi

# Dialectical checkpoints
echo "DIALECTICAL CHECKPOINT: What dependencies are truly required?"
echo "DIALECTICAL CHECKPOINT: How do we verify the cache reproduces identical environments?"

# Ensure Poetry matches the lock file expectations. Poetry 2.2.1 introduced the
# `[project]` metadata layout used in this repository.
POETRY_REQUIRED_VERSION="2.2.1"
ensure_poetry() {
  local desired="$1"
  local current=""
  if command -v poetry >/dev/null 2>&1; then
    current="$(poetry --version | awk '{print $3}' | tr -d '()')"
    if [[ "$current" == "$desired" ]]; then
      return
    fi
    echo "[info] Poetry $current found; reinstalling $desired" >&2
  else
    echo "[info] Poetry not found; installing $desired" >&2
  fi
  run_check "pipx install poetry==$desired" pipx install --force "poetry==$desired"
}
ensure_poetry "$POETRY_REQUIRED_VERSION"

# Accept either the legacy 0.1.0-alpha.1 notation or the PEP 440-compliant
# 0.1.0a1 form. Normalize the current version to the latter for comparison so
# future releases can switch schemes without breaking setup. The project version
# moved from `[tool.poetry]` to `[project]`; handle both layouts for resiliency.
EXPECTED_VERSION="0.1.0a1"
CURRENT_VERSION="$(python - <<'PY'
import sys
import tomllib

with open('pyproject.toml', 'rb') as handle:
    data = tomllib.load(handle)

version = (
    data.get('tool', {}).get('poetry', {}).get('version')
    or data.get('project', {}).get('version')
)

if not version:
    raise SystemExit('Unable to determine project version from pyproject.toml')

print(version)
PY
)"
NORMALIZED_VERSION="${CURRENT_VERSION/-alpha./a}"
if [[ "$NORMALIZED_VERSION" != "$EXPECTED_VERSION" ]]; then
  echo "Project version $CURRENT_VERSION does not match $EXPECTED_VERSION" >&2
  exit 1
fi

POETRY_CHECK_LOG="$(mktemp)"
if ! poetry check >"$POETRY_CHECK_LOG" 2>&1; then
  cat "$POETRY_CHECK_LOG"
  echo "[error] Poetry metadata check failed. Run 'poetry lock' to refresh the lock file or resolve the reported issues." >&2
  exit 1
fi
rm -f "$POETRY_CHECK_LOG"

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
  --all-extras \
  --no-interaction

python "$PROJECT_ROOT/scripts/verify_post_install.py"

# Ensure prometheus-client is available after installation
poetry run python -c "import prometheus_client"
# Handle normalized package names with underscores
poetry run pip list | grep prometheus-client >/dev/null || \
  poetry run pip list | grep prometheus_client >/dev/null

# Install the DevSynth CLI with pipx and verify it works. On subsequent
# runs, skip the installation step to avoid network access.
if command -v devsynth >/dev/null; then
  echo "[info] devsynth CLI already installed; skipping pipx install"
elif [[ "${PIP_NO_INDEX:-0}" == "1" ]]; then
  echo "[warning] offline mode detected; skipping pipx install" >&2
else
  if ! pipx install --editable . --force; then
    echo "[warning] pipx install failed" >&2
  else
    poetry run pip freeze > /tmp/devsynth-requirements.txt
    pipx runpip devsynth install -r /tmp/devsynth-requirements.txt || \
      echo "[warning] pipx runpip devsynth failed" >&2
  fi
fi

if command -v devsynth >/dev/null; then
  devsynth --help >/dev/null || echo "[warning] devsynth --help failed"
else
  echo "[warning] devsynth CLI unavailable; skipping CLI checks" >&2
fi

# Validate dependency installation
PIP_NO_INDEX=1 poetry run pip check

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

# Confirm GPU extras remain excluded by default
poetry run python - <<'EOF'
import importlib.util, sys
GPU_PACKAGES = ["torch", "transformers"]
installed = [pkg for pkg in GPU_PACKAGES if importlib.util.find_spec(pkg)]
if installed:
    sys.exit("GPU extras unexpectedly installed: " + ", ".join(installed))
EOF

# Ensure dependency tree is healthy after installing extras
PIP_NO_INDEX=1 poetry run pip check

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
# hangs while the log aids in diagnosing failures. Keeping this step under
# ten minutes helps the overall setup stay within the target runtime.
# What evidence shows the CLI can run tests non-interactively?
timeout 10m poetry run devsynth run-tests --speed=fast | tee devsynth_cli_tests.log

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
run_check "Security audit" DEVSYNTH_PRE_DEPLOY_APPROVED=true poetry run python scripts/security_audit.py

# Final checks to confirm task and DevSynth CLI availability
task --version
poetry run devsynth --help

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo "codex_setup completed in ${ELAPSED}s"
if (( ELAPSED > MAX_SECONDS )); then
  echo "codex_setup exceeded ${MAX_SECONDS}s limit" >&2
  exit 1
elif (( ELAPSED > WARN_SECONDS )); then
  echo "[warning] codex_setup exceeded ${WARN_SECONDS}s target" >&2
fi
