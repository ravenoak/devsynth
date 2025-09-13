#!/usr/bin/env bash
set -euo pipefail

# Platform guard: this script targets Linux/macOS. On Windows, use WSL2 (Ubuntu) and run inside the WSL shell.
os_name="$(uname -s 2>/dev/null || echo unknown)"
case "$os_name" in
  MINGW*|MSYS*|CYGWIN*|Windows*)
    echo "[error] Windows shell detected ($os_name). This script supports Linux and macOS shells only." >&2
    echo "[hint] Please use Windows Subsystem for Linux (WSL2) with Ubuntu and run this script inside the WSL shell." >&2
    echo "[docs] See docs/getting_started/installation.md#windows--wsl2 for instructions." >&2
    exit 1 ;;
  Linux|Darwin)
    : ;;
  *)
    echo "[warning] Unrecognized OS: $os_name. Proceeding, but this script is designed for Linux/macOS." >&2 ;;
esac

CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/devsynth"
WHEEL_DIR="$CACHE_DIR/wheels"
mkdir -p "$WHEEL_DIR"

# Abort if the active Python version is below 3.12
if ! py_ver="$(python --version 2>&1)"; then
  echo "[error] unable to determine Python version" >&2
  exit 1
fi
if [[ $py_ver =~ ^Python[[:space:]]([0-9]+)\.([0-9]+) ]]; then
  major="${BASH_REMATCH[1]}"
  minor="${BASH_REMATCH[2]}"
  if (( major < 3 || (major == 3 && minor < 12) )); then
    echo "[error] Python 3.12 or higher is required; found $py_ver" >&2
    exit 1
  fi
else
  echo "[error] unrecognized Python version output: $py_ver" >&2
  exit 1
fi

# Ensure go-task is available for Taskfile-based workflows
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
  if ! command -v task >/dev/null 2>&1; then
    echo "[error] task binary not found on PATH after installation" >&2
    exit 1
  fi
  if ! task --version >/dev/null 2>&1; then
    echo "[error] task command failed to run after installation" >&2
    exit 1
  fi
  task_path="$(command -v task)"
  if [[ "$task_path" != "$TASK_BIN_DIR/task" ]]; then
    echo "[error] task installed to unexpected location: $task_path" >&2
    exit 1
  fi
fi

# Ensure the Task binary directory is on PATH for current and future sessions
if [[ ":$PATH:" != *":$TASK_BIN_DIR:"* ]]; then
  export PATH="$TASK_BIN_DIR:$PATH"
fi
if [ -w "$HOME/.profile" ] && ! grep -F "$TASK_BIN_DIR" "$HOME/.profile" >/dev/null 2>&1; then
  echo "export PATH=\"$TASK_BIN_DIR:\$PATH\"" >> "$HOME/.profile"
fi
echo "$TASK_BIN_DIR" >> "${GITHUB_PATH:-/dev/null}" 2>/dev/null || true

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

# Ensure Poetry is installed and manages a dedicated virtual environment
if ! command -v poetry >/dev/null 2>&1; then
  echo "[info] poetry not found; installing Poetry via official installer" >&2
  if command -v curl >/dev/null 2>&1; then
    curl -sSL https://install.python-poetry.org | python - >/tmp/poetry_install.log 2>&1 || {
      echo "[error] Poetry installation failed" >&2; exit 1; }
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- https://install.python-poetry.org | python - >/tmp/poetry_install.log 2>&1 || {
      echo "[error] Poetry installation failed" >&2; exit 1; }
  else
    echo "[error] neither curl nor wget is available to install Poetry" >&2
    exit 1
  fi
  # Add Poetry to PATH for current session and GitHub Actions if available
  export PATH="$HOME/.local/bin:$PATH"
  echo "$HOME/.local/bin" >> "${GITHUB_PATH:-/dev/null}" 2>/dev/null || true
fi

if ! poetry --version >/dev/null 2>&1; then
  echo "[error] poetry command not working after installation" >&2
  exit 1
fi

poetry config virtualenvs.create true
poetry env remove --all >/dev/null 2>&1 || true
# Prefer an explicit Python 3.12 interpreter. Fall back to the active python
# if pyenv does not expose a dedicated shim.
py_exec=""
if command -v pyenv >/dev/null 2>&1; then
  py_exec="$(pyenv which python3.12 2>/dev/null || true)"
fi
if [[ -z "$py_exec" ]]; then
  py_exec="$(command -v python3.12 2>/dev/null || command -v python)"
fi
if ! poetry env use "$py_exec" >/dev/null 2>&1; then
  echo "[error] Python 3.12 executable not available for Poetry: $py_exec" >&2
  exit 1
fi

export PIP_FIND_LINKS="$WHEEL_DIR"

# Install DevSynth with development dependencies and all optional extras if the CLI is missing
if ! poetry run devsynth --help >/dev/null 2>&1; then
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

  poetry install --with dev --all-extras
else
  echo "[info] devsynth CLI already present; skipping poetry install" >&2
fi

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

# Confirm the DevSynth CLI entry point is available
if ! poetry run devsynth --help >/dev/null 2>&1; then
  echo "[error] devsynth console script not found" >&2
  echo "[hint] try rerunning 'poetry install --with dev --all-extras'" >&2
  exit 1
fi

# Install pre-commit hooks to enable repository checks
poetry run pre-commit install --install-hooks

# Verify dependencies offline
PIP_NO_INDEX=1 poetry run pip check

# Run repository verification commands
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p benchmark"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=0

# Confirm environment and task availability before tests
if ! poetry env info --path >/dev/null 2>&1; then
  echo "[error] poetry virtualenv path not found before tests" >&2
  exit 1
fi
if ! task --version >/dev/null 2>&1; then
  echo "[error] task command not available before tests" >&2
  exit 1
fi

poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
# Re-run to guarantee deterministic results via caching
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py

task --version
poetry run devsynth --help
