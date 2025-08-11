#!/usr/bin/env bash
set -euo pipefail
umask 077
IFS=$'\n\t'

# Bootstrap the local DevSynth environment.
# Builds and starts DevSynth along with monitoring stack.

# Refuse to run as root to avoid privilege escalation issues.
if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
  exit 1
fi

# Require execution from repository root to avoid path traversal issues.
if [[ ! -f pyproject.toml ]]; then
  echo "Run this script from the repository root." >&2
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

# Verify .env file is not a symlink and permissions are restricted if it exists.
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

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d --build --pull=always
