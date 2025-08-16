#!/usr/bin/env bash
set -euo pipefail

# Simple health check for DevSynth containers
# Usage: check_health.sh [environment]
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

echo "Checking container health for profile: ${ENVIRONMENT}"

UNHEALTHY=$(docker compose --env-file "$ENV_FILE" --profile "${ENVIRONMENT}" ps --format '{{.Name}} {{.State}} {{.Health}}' | awk '$3 != "healthy"')
if [[ -n "${UNHEALTHY}" ]]; then
  echo "Unhealthy services detected:"
  echo "${UNHEALTHY}"
  exit 1
fi

curl -sf http://localhost:8000/health >/dev/null && echo "API healthy" || { echo "API unhealthy"; exit 1; }
