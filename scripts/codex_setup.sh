set -exo pipefail

# Use Python 3.12 if available, otherwise fall back to Python 3.11
poetry env use "$(command -v python3.12 || command -v python3.11)"

# Install only the extras required for the test suite. Large GPU packages
# provided by the `offline` extra are intentionally excluded to keep setup
# fast. Add the `offline` extra manually if GPU features are needed.
poetry install \
  --with dev,docs \
  --all-extras \
  --no-interaction

# Verify key packages are present
poetry run python - <<'EOF'
import importlib
import sys

required = ["pytest", "pytest_bdd", "pydantic", "yaml", "typer"]
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

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED
