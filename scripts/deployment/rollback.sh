#!/usr/bin/env bash
set -euo pipefail

# Roll back DevSynth to a previous image tag.
# Usage: rollback.sh <previous_tag> [environment]
#   previous_tag: required image tag to roll back to
#   environment: development (default), staging, production, testing

PREVIOUS_TAG=${1:-}
ENVIRONMENT=${2:-development}

if [[ -z "$PREVIOUS_TAG" ]]; then
  echo "Usage: rollback.sh <previous_tag> [environment]" >&2
  exit 1
fi

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

# Ensure Docker is available
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but could not be found in PATH." >&2
  exit 1
fi

ENV_FILE=".env.${ENVIRONMENT}"
if [[ -f "$ENV_FILE" ]] && [[ $(stat -c %a "$ENV_FILE") != "600" ]]; then
  echo "Environment file $ENV_FILE must have 600 permissions" >&2
  exit 1
fi

# Stop the current stack
"$(dirname "$0")/stop_stack.sh" "$ENVIRONMENT"

# Pull the specified tag and restart the service
export DEVSYNTH_IMAGE_TAG="$PREVIOUS_TAG"
docker compose --env-file "$ENV_FILE" --profile "${ENVIRONMENT}" pull devsynth
docker compose --env-file "$ENV_FILE" --profile "${ENVIRONMENT}" up -d devsynth

# Verify services are healthy
"$(dirname "$0")/health_check.sh"
