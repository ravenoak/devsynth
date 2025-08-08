#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Check the health of DevSynth services.
# Verifies API and monitoring endpoints respond successfully.

if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
  exit 1
fi

command -v curl >/dev/null 2>&1 || {
  echo "curl is required but not installed." >&2
  exit 1
}

curl -fsS --max-time 10 http://localhost:8000/health > /dev/null
curl -fsS --max-time 10 http://localhost:3000/api/health > /dev/null

echo "All services are healthy"
