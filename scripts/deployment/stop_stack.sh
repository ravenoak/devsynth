#!/usr/bin/env bash
set -euo pipefail

# Stop DevSynth stack
# Usage: stop_stack.sh [environment]
#   environment: development (default), staging, production, testing

ENVIRONMENT=${1:-development}

# Enforce non-root execution for least privilege
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

ENV_FILE=".env.${ENVIRONMENT}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing environment file: $ENV_FILE" >&2
  exit 1
fi
if [[ $(stat -c %a "$ENV_FILE") != "600" ]]; then
  echo "Environment file $ENV_FILE must have 600 permissions" >&2
  exit 1
fi

# Export for docker compose variable substitution
export ENV_FILE

# Ensure Docker is available
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but could not be found in PATH." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose is required but unavailable." >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" --profile "${ENVIRONMENT}" --profile monitoring down
