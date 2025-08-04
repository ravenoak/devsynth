set -exo pipefail

# NOTE: This script provisions the Codex testing environment only. It is not
# intended for regular development setup.

# Ensure pipx is available for installing the CLI
if ! command -v pipx >/dev/null; then
  apt-get update && apt-get install -y pipx
fi
export PATH="$HOME/.local/bin:$PATH"
pipx ensurepath

# Use Python 3.12 if available, otherwise fall back to Python 3.11
poetry env use "$(command -v python3.12 || command -v python3.11)"

# Verify that the virtual environment was created
poetry env info --path >/dev/null

# Install only the extras required for the test suite. Large GPU packages
# provided by the `offline` extra are intentionally excluded to keep setup
# fast. Add the `offline` extra manually if GPU features are needed.
poetry install \
  --with dev,docs \
  -E docs \
  -E minimal \
  -E retrieval \
  -E chromadb \
  -E lmstudio \
  -E memory \
  -E llm \
  -E api \
  -E webui \
  -E gui \
  -E tests \
  --no-interaction

# Install the DevSynth CLI with pipx and verify it works
pipx install --editable . --force
poetry run pip freeze > /tmp/devsynth-requirements.txt
pipx runpip devsynth install -r /tmp/devsynth-requirements.txt
command -v devsynth >/dev/null
devsynth --version || echo "[warning] devsynth --version failed"

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

# Verify key packages are present
poetry run python - <<'EOF'
import importlib
import sys

required = ["pytest", "pytest_bdd", "pydantic", "yaml", "typer", "tiktoken", "chromadb"]
missing = []
for pkg in required:
    try:
        importlib.import_module(pkg)
    except Exception:
        missing.append(pkg)
if missing:
    sys.exit("Missing packages: " + ", ".join(missing))
EOF

# Kuzu is optional; skip related tests if it's not installed
if ! poetry run python -c "import kuzu" >/dev/null 2>&1; then
  echo "[warning] kuzu package not installed; kuzu tests will be skipped"
  export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=false
fi

# Double-check that pytest-bdd can be imported
poetry run python -c "import pytest_bdd"

# Ensure pytest-bdd is installed in the environment
poetry run pip list | grep pytest-bdd >/dev/null

# Run a smoke test to catch failures early
poetry run pytest --maxfail=1

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED
