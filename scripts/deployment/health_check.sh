#!/usr/bin/env bash
set -euo pipefail

# Check the health of DevSynth services.
# Verifies API and monitoring endpoints respond successfully.
# Usage: health_check.sh [api_url] [grafana_url]

API_URL=${1:-http://localhost:8000/health}
GRAFANA_URL=${2:-http://localhost:3000/api/health}

if [[ "$EUID" -eq 0 ]]; then
  echo "Please run this script as a non-root user." >&2
  exit 1
fi

for url in "$API_URL" "$GRAFANA_URL"; do
  if [[ ! "$url" =~ ^https?:// ]]; then
    echo "Invalid URL: $url" >&2
    exit 1
  fi
  if ! curl -fsS "$url" > /dev/null; then
    echo "Health check failed for $url" >&2
    exit 1
  fi
done

echo "All services are healthy"
