set -exo pipefail

# Install the minimal runtime and development packages needed for tests.
# Optional extras enable memory and LLM providers so pytest can run
# without manual intervention in the offline environment.
poetry install \
  --with dev \
  --extras minimal \
  --extras memory \
  --extras llm \
  --no-interaction

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
