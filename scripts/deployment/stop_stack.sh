#!/usr/bin/env bash
set -euo pipefail

# Stop DevSynth stack
# Usage: stop_stack.sh [environment]
#   environment: development (default), staging, production, testing

ENVIRONMENT=${1:-development}

docker compose --profile "${ENVIRONMENT}" --profile monitoring down
