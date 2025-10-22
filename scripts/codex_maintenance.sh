#!/usr/bin/env bash
set -exo pipefail

START_TIME=$(date +%s)
MAX_SECONDS=$((10 * 60))
WARN_SECONDS=$((5 * 60))

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$PWD" != "$PROJECT_ROOT" ]]; then
  cd "$PROJECT_ROOT"
fi

PIPX_BIN_DIR="$HOME/.local/bin"
if [[ ":$PATH:" != *":$PIPX_BIN_DIR:"* ]]; then
  export PATH="$PIPX_BIN_DIR:$PATH"
fi
pipx ensurepath
if [ -w "$HOME/.profile" ] && ! grep -F "$PIPX_BIN_DIR" "$HOME/.profile" >/dev/null 2>&1; then
  echo "export PATH=\"$PIPX_BIN_DIR:\$PATH\"" >> "$HOME/.profile"
fi

run_check() {
  local desc="$1"
  shift
  if ! "$@"; then
    echo "$desc failed" >&2
    exit 1
  fi
}

# Ensure the Poetry CLI matches the lock file expectations.
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

if ! command -v python3.12 >/dev/null; then
  echo "Python 3.12 is required for maintenance" >&2
  exit 1
fi

poetry env use "$(command -v python3.12)"
poetry env info --path >/dev/null

EXPECTED_VERSION="0.1.0a1"
CURRENT_VERSION="$(python - <<'PY'
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

run_check "Dependency synchronization" poetry install \
  --with dev \
  --all-extras \
  --no-interaction \
  --sync

run_check "Post-install verification" poetry run python scripts/verify_post_install.py
run_check "pip check" PIP_NO_INDEX=1 poetry run pip check

# Quick health probes instead of the full suite from codex_setup.sh.
poetry run devsynth doctor --no-input || echo "[warning] devsynth doctor reported issues" >&2
poetry run python scripts/verify_version_sync.py

if [ -f CODEX_ENVIRONMENT_MAINTENANCE_FAILED ]; then
  rm CODEX_ENVIRONMENT_MAINTENANCE_FAILED
fi

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
echo "codex_maintenance completed in ${ELAPSED}s"
if (( ELAPSED > MAX_SECONDS )); then
  echo "codex_maintenance exceeded ${MAX_SECONDS}s limit" >&2
  exit 1
elif (( ELAPSED > WARN_SECONDS )); then
  echo "[warning] codex_maintenance exceeded ${WARN_SECONDS}s target" >&2
fi
