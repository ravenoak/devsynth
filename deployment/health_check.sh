#!/usr/bin/env bash
set -euo pipefail
umask 077
IFS=$'\n\t'

# Check the health of DevSynth services.
# Verifies API and monitoring endpoints respond successfully.

if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
  exit 1
fi

# Require execution from repository root to avoid path traversal issues.
if [[ ! -f pyproject.toml ]]; then
  echo "Run this script from the repository root." >&2
  exit 1
fi

command -v curl >/dev/null 2>&1 || {
  echo "curl is required but not installed." >&2
  exit 1
}

# Ensure any .env file is secure if present.
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

curl -fsS --max-time 10 http://localhost:8000/health > /dev/null
curl -fsS --max-time 10 http://localhost:3000/api/health > /dev/null

echo "All services are healthy"
