#!/usr/bin/env bash
set -euo pipefail

# Start DevSynth stack with monitoring
# Usage: start_stack.sh [environment]
#   environment: development (default), staging, production, testing

ENVIRONMENT=${1:-development}

docker compose --profile "${ENVIRONMENT}" --profile monitoring up -d

# Verify container health
"$(dirname "$0")/check_health.sh" "${ENVIRONMENT}"
