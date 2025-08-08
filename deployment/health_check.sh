#!/usr/bin/env bash
set -euo pipefail

# Check the health of DevSynth services.
# Verifies API and monitoring endpoints respond successfully.

curl -fsS --max-time 10 http://localhost:8000/health > /dev/null
curl -fsS --max-time 10 http://localhost:3000/api/health > /dev/null

echo "All services are healthy"
