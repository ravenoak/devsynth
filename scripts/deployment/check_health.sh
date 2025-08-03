#!/usr/bin/env bash
set -euo pipefail

# Simple health check for DevSynth containers
# Usage: check_health.sh [environment]
#   environment: development (default), staging, production, testing

ENVIRONMENT=${1:-development}

echo "Checking container health for profile: ${ENVIRONMENT}"

UNHEALTHY=$(docker compose --profile "${ENVIRONMENT}" ps --format '{{.Name}} {{.State}} {{.Health}}' | awk '$3 != "healthy"')
if [[ -n "${UNHEALTHY}" ]]; then
  echo "Unhealthy services detected:"
  echo "${UNHEALTHY}"
  exit 1
fi

curl -f http://localhost:8000/health >/dev/null && echo "API healthy" || { echo "API unhealthy"; exit 1; }
