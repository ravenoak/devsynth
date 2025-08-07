#!/usr/bin/env bash
set -euo pipefail

# Check the health of DevSynth services.
# Verifies API and monitoring endpoints respond successfully.

curl -fsS http://localhost:8000/health > /dev/null
curl -fsS http://localhost:3000/api/health > /dev/null

echo "All services are healthy"
