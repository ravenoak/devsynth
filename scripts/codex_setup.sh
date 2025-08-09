set -exo pipefail

# NOTE: This script provisions the Codex testing environment only. It is not
# intended for regular development setup.

# Ensure pipx is available for installing the CLI. When rerunning offline,
# skip installation if pipx is already present so the script can proceed
# without network access.
if ! command -v pipx >/dev/null; then
  if command -v apt-get >/dev/null; then
    if ! (apt-get update && apt-get install -y pipx); then
      echo "[warning] failed to install pipx" >&2
    fi
  else
    echo "[warning] apt-get unavailable; pipx not installed" >&2
  fi
fi
export PATH="$HOME/.local/bin:$PATH"
pipx ensurepath

# Use Python 3.12 if available, otherwise fall back to Python 3.11
poetry env use "$(command -v python3.12 || command -v python3.11)"

# Verify that the virtual environment was created
poetry env info --path >/dev/null

# Install development dependencies and test extras. Large GPU packages provided
# by the `offline` extra are intentionally excluded to keep setup fast. Add the
# `offline` extra manually if GPU features are needed.
poetry install \
  --with dev \
  --extras tests \
  --no-interaction

# Ensure prometheus-client is available after installation
poetry run python -c "import prometheus_client"
# Handle normalized package names with underscores
poetry run pip list | grep prometheus-client >/dev/null || \
  poetry run pip list | grep prometheus_client >/dev/null

# Install the DevSynth CLI with pipx and verify it works. On subsequent
# runs, skip the installation step to avoid network access.
if ! command -v devsynth >/dev/null; then
  pipx install --editable . --force
fi
poetry run pip freeze > /tmp/devsynth-requirements.txt
pipx runpip devsynth install -r /tmp/devsynth-requirements.txt || \
  echo "[warning] pipx runpip devsynth failed" >&2
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
    "chromadb",
    "fastapi",
    "streamlit",
    "lmstudio",
    "tinydb",
    "duckdb",
    "lmdb",
    "kuzu",
    "faiss",
    "prometheus_client",
    "httpx",
    "dearpygui",
]
missing = []
for pkg in required:
    try:
        importlib.import_module(pkg)
    except Exception:
        missing.append(pkg)
if missing:
    sys.exit("Missing packages: " + ", ".join(missing))
EOF

# Ensure dependency tree is healthy after installing extras
poetry run pip check

# Kuzu is optional; skip related tests if it's not installed
if ! poetry run python -c "import kuzu" >/dev/null 2>&1; then
  echo "[warning] kuzu package not installed; kuzu tests will be skipped"
  export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=false
fi

# Run a smoke test to catch failures early
poetry run pytest tests/behavior/steps/test_alignment_metrics_steps.py --maxfail=1

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED
