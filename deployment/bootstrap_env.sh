#!/usr/bin/env bash
set -euo pipefail

# Bootstrap the local DevSynth environment.
# Builds and starts DevSynth along with monitoring stack.

docker compose -f deployment/docker-compose.yml -f deployment/docker-compose.monitoring.yml up -d --build --pull=always
