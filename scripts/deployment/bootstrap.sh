#!/usr/bin/env bash
set -euo pipefail

# Build images and start the DevSynth stack.
# Usage: bootstrap.sh [environment]
#   environment: development (default), staging, production, testing

ENVIRONMENT=${1:-development}

# Refuse to run as root
if [[ "$EUID" -eq 0 ]]; then
  echo "Please run this script as a non-root user." >&2
  exit 1
fi

# Allow only known environments
ALLOWED_ENVIRONMENTS=(development staging production testing)
if [[ ! " ${ALLOWED_ENVIRONMENTS[*]} " =~ " ${ENVIRONMENT} " ]]; then
  echo "Invalid environment: ${ENVIRONMENT}" >&2
  exit 1
fi

# Ensure Docker is available before continuing
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but could not be found in PATH." >&2
  exit 1
fi

ENV_FILE=".env.${ENVIRONMENT}"
if [[ -f "$ENV_FILE" ]] && [[ $(stat -c %a "$ENV_FILE") != "600" ]]; then
  echo "Environment file $ENV_FILE must have 600 permissions" >&2
  exit 1
fi

# Pull latest base images and build the current compose configuration
docker compose pull
docker compose build

# Start the stack for the requested environment
"$(dirname "$0")/start_stack.sh" "$ENVIRONMENT"

# Perform a simple service health check
"$(dirname "$0")/health_check.sh"
