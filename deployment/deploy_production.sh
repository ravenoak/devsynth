#!/usr/bin/env bash
set -euo pipefail
umask 077
IFS=$'\n\t'

# Build and run DevSynth in production mode

# Refuse to run as root for better security.
if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
  exit 1
fi

# Require execution from repository root to avoid path traversal issues.
if [[ ! -f pyproject.toml ]]; then
  echo "Run this script from the repository root." >&2
  exit 1
fi

# Ensure docker and compose are available
command -v docker >/dev/null 2>&1 || {
  echo "docker is required but not installed." >&2
  exit 1
}
command -v docker compose >/dev/null 2>&1 || {
  echo "docker compose plugin is required." >&2
  exit 1
}

# Run policy checks before deployment
command -v poetry >/dev/null 2>&1 || {
  echo "poetry is required but not installed." >&2
  exit 1
}
poetry run python scripts/security_audit.py

# Ensure sensitive env files are not world-readable or symlinks
if [[ -f .env ]]; then
  if [[ -L .env ]]; then
    echo ".env should not be a symlink." >&2
    exit 1
  fi
  if [[ $(stat -c '%a' .env) -gt 600 ]]; then
    echo ".env file permissions are too permissive; run 'chmod 600 .env'." >&2
    exit 1
  fi
fi

# Ensure required security token is present.
if [[ -z "${DEVSYNTH_ACCESS_TOKEN:-}" ]]; then
  echo "DEVSYNTH_ACCESS_TOKEN must be set." >&2
  exit 1
fi

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml build --pull --no-cache

docker compose -f docker-compose.production.yml up -d --pull=always
