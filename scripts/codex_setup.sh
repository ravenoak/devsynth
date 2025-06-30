set -exo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  build-essential python3-dev python3-venv cmake pkg-config git \
  libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev \
  liblapack-dev libopenblas-dev liblmdb-dev libz3-dev libcurl4-openssl-dev
apt-get clean
rm -rf /var/lib/apt/lists/*

# Install all project dependencies including optional groups
poetry install --all-extras --with dev,docs

# Verify that core and development packages are available
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
