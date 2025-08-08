#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Build and run DevSynth in production mode

# Refuse to run as root for better security.
if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
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

# Ensure sensitive env files are not world-readable
if [[ -f .env ]] && [[ $(stat -c '%a' .env) -gt 600 ]]; then
  echo ".env file permissions are too permissive; run 'chmod 600 .env'." >&2
  exit 1
fi

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml build --pull --no-cache

docker compose -f docker-compose.production.yml up -d --pull=always
