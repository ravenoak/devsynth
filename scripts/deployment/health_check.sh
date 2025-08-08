#!/usr/bin/env bash
set -euo pipefail

# Check the health of DevSynth services.
# Verifies API and monitoring endpoints respond successfully.
# Usage: health_check.sh [api_url] [grafana_url]

API_URL=${1:-http://localhost:8000/health}
GRAFANA_URL=${2:-http://localhost:3000/api/health}

curl -fsS "$API_URL" > /dev/null
curl -fsS "$GRAFANA_URL" > /dev/null

echo "All services are healthy"
