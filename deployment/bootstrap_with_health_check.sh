#!/usr/bin/env bash
set -euo pipefail
umask 077
IFS=$'\n\t'

# Bootstrap the DevSynth environment and verify service health.

if [[ $EUID -eq 0 ]]; then
  echo "This script should not be run as root." >&2
  exit 1
fi

if [[ ! -f pyproject.toml ]]; then
  echo "Run this script from the repository root." >&2
  exit 1
fi

# Ensure required security token is present.
if [[ -z "${DEVSYNTH_ACCESS_TOKEN:-}" ]]; then
  echo "DEVSYNTH_ACCESS_TOKEN must be set." >&2
  exit 1
fi

# Build and start services, then run health checks.
./deployment/bootstrap_env.sh
./deployment/health_check.sh
