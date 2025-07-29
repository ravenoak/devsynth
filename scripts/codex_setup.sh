set -exo pipefail

# NOTE: This script provisions the Codex testing environment only. It is not
# intended for regular development setup.

# Use Python 3.12 if available, otherwise fall back to Python 3.11
poetry env use "$(command -v python3.12 || command -v python3.11)"

# Install only the extras required for the test suite. Large GPU packages
# provided by the `offline` extra are intentionally excluded to keep setup
# fast. Add the `offline` extra manually if GPU features are needed.
poetry install \
  --with dev,docs \
  --all-extras \
  --no-interaction

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

required = ["pytest", "pytest_bdd", "pydantic", "yaml", "typer", "tiktoken"]
missing = []
for pkg in required:
    try:
        importlib.import_module(pkg)
    except Exception:
        missing.append(pkg)
if missing:
    sys.exit("Missing packages: " + ", ".join(missing))
EOF

# Double-check that pytest-bdd can be imported
poetry run python -c "import pytest_bdd"

# Ensure pytest-bdd is installed in the environment
poetry run pip show pytest-bdd >/dev/null

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED
