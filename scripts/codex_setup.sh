set -exo pipefail

# Use Python 3.12 if available, otherwise fall back to Python 3.11
poetry env use "$(command -v python3.12 || command -v python3.11)"

# Install dependencies. Use --minimal to skip docs but still include all extras.
if [[ "$1" == "--minimal" ]]; then
  poetry install \
    --with dev \
    --all-extras \
    --no-interaction
else
  # Install all optional extras along with the dev and docs dependency groups.
  # This ensures memory and LLM providers are available for the test suite.
  poetry install \
    --with dev,docs \
    --all-extras \
    --no-interaction
fi

# Verify key packages are present
poetry run python - <<'EOF'
import sys
import pkg_resources

required = ["typer", "pytest"]
missing = [pkg for pkg in required if pkg not in {d.key for d in pkg_resources.working_set}]
if missing:
    sys.exit(f"Missing packages: {', '.join(missing)}")
EOF

# Cleanup any failure marker if the setup completes successfully
[ -f CODEX_ENVIRONMENT_SETUP_FAILED ] && rm CODEX_ENVIRONMENT_SETUP_FAILED
