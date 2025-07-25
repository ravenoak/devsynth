#!/usr/bin/env bash
set -euo pipefail

# Build and run DevSynth in production mode

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml build

docker compose -f docker-compose.production.yml up -d
