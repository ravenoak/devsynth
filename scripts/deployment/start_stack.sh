#!/usr/bin/env bash
set -euo pipefail

# Start DevSynth stack with monitoring

docker compose -f docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d
