#!/usr/bin/env bash
set -euo pipefail

INSTALL_DEV_TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CLI_TYPER_VERSION="0.17.4"

if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  cd "$PROJECT_ROOT"
fi

DIAGNOSTICS_DIR="$PROJECT_ROOT/diagnostics"
mkdir -p "$DIAGNOSTICS_DIR"

PREFETCH_OPTIONAL_WHEELS=0

sanitize_slug() {
  local input="$1"
  local lower slug
  lower="$(printf '%s' "$input" | tr '[:upper:]' '[:lower:]')"
  slug="$(printf '%s' "$lower" | sed -e 's/[^a-z0-9_-]/-/g' -e 's/-\{2,\}/-/g' -e 's/^-//' -e 's/-$//')"
  if [[ -z "$slug" ]]; then
    slug="phase"
  fi
  printf '%s\n' "$slug"
}

prefetch_optional_wheels() {
  if [[ "$PREFETCH_OPTIONAL_WHEELS" == "1" ]]; then
    return 0
  fi

  local optional_pkgs
  optional_pkgs=$(python - <<'PY'
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

  if [[ -z "$optional_pkgs" ]]; then
    PREFETCH_OPTIONAL_WHEELS=1
    return 0
  fi

  local missing_pkgs=()
  local pkg
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

  PREFETCH_OPTIONAL_WHEELS=1
}

run_poetry_install() {
  local attempt="$1"
  local phase="$2"
  local timestamp="$3"
  local phase_slug
  phase_slug="$(sanitize_slug "$phase")"
  local log_path="$DIAGNOSTICS_DIR/poetry_install_${phase_slug}_attempt${attempt}_${timestamp}.log"

  echo "[info] running 'poetry install --with dev --all-extras' during $phase (attempt $attempt); output logged to $log_path" >&2

  prefetch_optional_wheels

  if ! poetry install --with dev --all-extras 2>&1 | tee "$log_path"; then
    echo "[error] 'poetry install --with dev --all-extras' failed during $phase (attempt $attempt). See $log_path" >&2
    return 1
  fi

  return 0
}

run_targeted_reinstall() {
  local attempt="$1"
  local phase="$2"
  local timestamp="$3"
  local phase_slug
  phase_slug="$(sanitize_slug "$phase")"
  local log_path="$DIAGNOSTICS_DIR/pip_reinstall_${phase_slug}_attempt${attempt}_${timestamp}.log"

  echo "[info] attempting targeted repair during $phase (attempt $attempt); output logged to $log_path" >&2

  if ! bash -o pipefail -c "poetry run pip install --force-reinstall . 2>&1 | tee '$log_path'"; then
    echo "[error] targeted reinstall of devsynth failed during $phase (attempt $attempt). See $log_path" >&2
    return 1
  fi

  if ! bash -o pipefail -c "poetry run pip install --force-reinstall typer==${CLI_TYPER_VERSION} 2>&1 | tee -a '$log_path'"; then
    echo "[error] targeted reinstall of typer failed during $phase (attempt $attempt). See $log_path" >&2
    return 1
  fi

  return 0
}

ensure_devsynth_cli() {
  local phase="$1"
  local phase_slug
  phase_slug="$(sanitize_slug "$phase")"

  local timestamp
  timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  local cli_log="$DIAGNOSTICS_DIR/post_install_${phase_slug}_verify1_${timestamp}.log"

  if python "$PROJECT_ROOT/scripts/verify_post_install.py" >"$cli_log" 2>&1; then
    rm -f "$cli_log"
    echo "[info] post-install verification succeeded during $phase; no reinstall required" >&2
    return 0
  fi

  echo "[warning] post-install verification failed during $phase; see $cli_log" >&2

  local repair_timestamp
  repair_timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  if ! run_targeted_reinstall "1" "$phase" "$repair_timestamp"; then
    echo "[error] targeted repair did not complete successfully during $phase" >&2
    return 1
  fi

  timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  cli_log="$DIAGNOSTICS_DIR/post_install_${phase_slug}_verify2_${timestamp}.log"
  if python "$PROJECT_ROOT/scripts/verify_post_install.py" >"$cli_log" 2>&1; then
    rm -f "$cli_log"
    echo "[info] post-install verification recovered after targeted repair during $phase" >&2
    return 0
  fi

  echo "[warning] post-install verification still failing during $phase after targeted repair; see $cli_log" >&2

  local reinstall_timestamp
  reinstall_timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  if ! run_poetry_install "2" "$phase" "$reinstall_timestamp"; then
    return 1
  fi

  timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
  cli_log="$DIAGNOSTICS_DIR/post_install_${phase_slug}_verify3_${timestamp}.log"
  if python "$PROJECT_ROOT/scripts/verify_post_install.py" >"$cli_log" 2>&1; then
    rm -f "$cli_log"
    echo "[info] post-install verification recovered after reinstall during $phase" >&2
    return 0
  fi

  echo "[error] post-install verification remains unsuccessful after $phase. See $cli_log" >&2
  return 1
}

append_profile_snippet() {
  local profile_path="$1"
  local label="$2"
  local snippet="$3"

  if [[ -z "$profile_path" || -z "$label" || -z "$snippet" ]]; then
    return 0
  fi

  local profile_dir
  profile_dir="$(dirname "$profile_path")"
  if [[ ! -d "$profile_dir" ]]; then
    return 0
  fi

  if [[ ! -e "$profile_path" ]]; then
    if ! touch "$profile_path" >/dev/null 2>&1; then
      echo "[warning] unable to update $profile_path for $label" >&2
      return 0
    fi
  fi

  if grep -F "$label" "$profile_path" >/dev/null 2>&1; then
    return 0
  fi

  {
    printf '\n# Added by DevSynth install_dev.sh (%s) on %s\n' "$label" "$INSTALL_DEV_TIMESTAMP"
    printf '%s\n' "$snippet"
  } >>"$profile_path"

  echo "[info] appended $label snippet to $profile_path" >&2
}

PROFILE_FILES=(
  "$HOME/.profile"
  "$HOME/.bash_profile"
  "$HOME/.bashrc"
  "$HOME/.zprofile"
  "$HOME/.zshrc"
)

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

# Ensure Task's installation directory is on PATH so an existing binary is detected
if [[ ":$PATH:" != *":$TASK_BIN_DIR:"* ]]; then
  export PATH="$TASK_BIN_DIR:$PATH"
fi

# Verify task binary; install go-task if the check fails
if ! task --version >/dev/null 2>&1; then
  echo "[info] task command missing or not functioning; installing go-task" >&2

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

  if ! [ -x "$TASK_BIN_DIR/task" ]; then
    echo "[error] task binary missing or not executable at $TASK_BIN_DIR/task" >&2
    exit 1
  fi

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

# Ensure the Task binary directory is on PATH for future sessions
task_path_snippet="export PATH=\"$TASK_BIN_DIR:\$PATH\""
for profile in "${PROFILE_FILES[@]}"; do
  append_profile_snippet "$profile" "devsynth-task-path" "$task_path_snippet"
done
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

poetry config virtualenvs.create true --local
poetry config virtualenvs.in-project true --local
export POETRY_VIRTUALENVS_IN_PROJECT=1

existing_env_path=""
if existing_env_path="$(poetry env info --path 2>/dev/null)"; then
  if [[ -n "$existing_env_path" && "$existing_env_path" != "$PROJECT_ROOT/.venv" ]]; then
    echo "[info] removing legacy Poetry virtualenv at $existing_env_path" >&2
    poetry env remove --all >/dev/null 2>&1 || true
  fi
else
  existing_env_path=""
fi
# Prefer an explicit Python 3.12 interpreter. Fall back to the active python
# if pyenv does not expose a dedicated shim.
py_exec=""
if command -v pyenv >/dev/null 2>&1; then
  py_exec="$(pyenv which python3.12 2>/dev/null || true)"
fi
if [[ -z "$py_exec" ]]; then
  py_exec="$(command -v python3.12 2>/dev/null || command -v python)"
fi
if [[ ! -d "$PROJECT_ROOT/.venv" ]]; then
  if ! "$py_exec" -m venv "$PROJECT_ROOT/.venv" >/dev/null 2>&1; then
    echo "[error] failed to create in-project virtualenv at $PROJECT_ROOT/.venv" >&2
    exit 1
  fi
  echo "[info] created in-project virtualenv at $PROJECT_ROOT/.venv" >&2
fi

if ! poetry env use "$PROJECT_ROOT/.venv/bin/python" >/dev/null 2>&1; then
  echo "[error] unable to activate Poetry virtualenv at $PROJECT_ROOT/.venv" >&2
  exit 1
fi

export PIP_FIND_LINKS="$WHEEL_DIR"

initial_install_timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
if ! run_poetry_install "1" "mandatory-bootstrap" "$initial_install_timestamp"; then
  echo "[error] unable to complete required poetry install. Review diagnostics/poetry_install_mandatory-bootstrap_* logs." >&2
  exit 1
fi

echo "[info] Before running tests manually, execute 'poetry install --with dev --extras \"tests retrieval chromadb api\"' to provision mandatory extras." >&2

if ! ensure_devsynth_cli "bootstrap"; then
  echo "[error] unable to verify the environment during bootstrap. Review diagnostics/post_install_bootstrap_* and poetry_install_bootstrap_* logs." >&2
  exit 1
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

if [[ "$venv_path" != "$PROJECT_ROOT/.venv" ]]; then
  echo "[info] poetry virtualenv is located at $venv_path (expected $PROJECT_ROOT/.venv)" >&2
fi

if [[ -d "$venv_path/bin" ]]; then
  echo "$venv_path/bin" >> "${GITHUB_PATH:-/dev/null}" 2>/dev/null || true
fi

# Confirm Poetry environment and DevSynth CLI remain healthy (auto-repair if checks fail)
if ! ensure_devsynth_cli "post-verification"; then
  echo "[error] post-install verification failed after running repository checks. Review diagnostics/post_install_post-verification_* and poetry_install_post-verification_* logs." >&2
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
