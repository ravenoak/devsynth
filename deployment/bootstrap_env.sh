#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Bootstrap the local DevSynth environment.
# Builds and starts DevSynth along with monitoring stack.

# Refuse to run as root to avoid privilege escalation issues.
if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
  exit 1
fi

# Ensure required tools are present.
command -v docker >/dev/null 2>&1 || {
  echo "docker is required but not installed." >&2
  exit 1
}
command -v docker compose >/dev/null 2>&1 || {
  echo "docker compose plugin is required." >&2
  exit 1
}

# Verify .env file permissions are restricted if it exists.
if [[ -f .env ]] && [[ $(stat -c '%a' .env) -gt 600 ]]; then
  echo ".env file permissions are too permissive; run 'chmod 600 .env'." >&2
  exit 1
fi

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d --build --pull=always
