#!/usr/bin/env bash
set -euo pipefail

# Simple health check for DevSynth API

curl -f http://localhost:8000/health && echo "API healthy" || { echo "API unhealthy"; exit 1; }
