#!/usr/bin/env bash
set -euo pipefail

# Build images and start the DevSynth stack.
# Usage: bootstrap.sh [environment]
#   environment: development (default), staging, production, testing

ENVIRONMENT=${1:-development}

# Build images for the current compose configuration

docker compose build

# Start the stack for the requested environment
"$(dirname "$0")/start_stack.sh" "$ENVIRONMENT"

# Perform a simple service health check
"$(dirname "$0")/health_check.sh"
