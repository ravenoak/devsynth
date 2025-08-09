#!/usr/bin/env bash
set -euo pipefail

# Bootstrap the local DevSynth environment.
# Builds and starts DevSynth along with monitoring stack.

# Refuse to run as root
if [[ "$EUID" -eq 0 ]]; then
  echo "Please run this script as a non-root user." >&2
  exit 1
fi

# Ensure Docker is available
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but could not be found in PATH." >&2
  exit 1
fi

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d --build
